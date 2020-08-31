import sys
import asyncio
from itertools import chain

import click
import boto3


def describe_instances():
    client = boto3.client("ec2")
    instances = client.describe_instances()
    return list(
        chain.from_iterable([r["Instances"] for r in instances["Reservations"]])
    )


def get_instance_id(instance):
    return instance["InstanceId"]


def get_name(instance):
    return [e["Value"] for e in instance["Tags"] if e["Key"] == "Name"][0]


def get_state(instance):
    return instance["State"]["Name"]


def get_private_ip(instance):
    return instance["NetworkInterfaces"][0]["PrivateIpAddress"]


STATE_COLORS = {
    "running": "green",
    "stopped": "red",
}


def colorize_state(state):
    return click.style(state, fg=STATE_COLORS.get(state, "yellow"))


###############################################################################
# Commands ####################################################################
###############################################################################
@click.group()
def cli():
    pass


@cli.command("ls")
@click.argument("name", default="")
@click.option("-s", "--state", default="", help="filtered by state if given")
def list_ec2_instances(name, state):
    instances = describe_instances()
    for i in instances:
        if (
            name.lower() in get_name(i).lower()
            and state.lower() in get_state(i).lower()
        ):
            click.echo(
                "\t".join(
                    [
                        get_instance_id(i),
                        get_name(i),
                        colorize_state(get_state(i)),
                        get_private_ip(i),
                    ]
                )
            )


async def start_instance(instance_id):
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)
    if instance.state["Name"] != "stopped":
        click.echo(f"Oops, ec2 instance({instance_id}) is not stopped.", err=True)
    instance.start()
    click.echo(f"ec2 instance({instance_id}) is now starting...", err=True)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, instance.wait_until_running)
    click.echo(f"ec2 instance({instance_id}) has started🚀", err=True)


@cli.command()
@click.argument("instance_ids", nargs=-1)
def start(instance_ids):
    """Start ec2 instances.

    Args:
        instance_ids: list of instance id to start
    """
    if not sys.stdin.isatty():
        # stdin from pipe
        instance_ids = click.get_text_stream("stdin").read().strip().split()

    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(*[start_instance(i) for i in instance_ids])
    loop.run_until_complete(tasks)


async def stop_instance(instance_id):
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)
    if instance.state["Name"] != "running":
        click.echo(f"Oops, ec2 instance({instance_id}) is not running.", err=True)
    instance.stop()
    click.echo(f"ec2 instance({instance_id}) is now stopping...", err=True)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, instance.wait_until_stopped)
    click.echo(f"ec2 instance({instance_id}) has stopped💤", err=True)


@cli.command()
@click.argument("instance_ids", nargs=-1)
def stop(instance_ids):
    """Stop ec2 instances.

    Args:
        instance_ids: list of instance id to stop
    """
    if not sys.stdin.isatty():
        # stdin from pipe
        instance_ids = click.get_text_stream("stdin").read().strip().split()

    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(*[stop_instance(i) for i in instance_ids])
    loop.run_until_complete(tasks)


def main():
    cli()


if __name__ == "__main__":
    main()
