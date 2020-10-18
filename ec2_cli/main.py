import asyncio
import sys
from itertools import chain

import boto3
import click


class Instance:
    def __init__(self, data):
        self._data = data

    @property
    def instance_id(self):
        return self._data["InstanceId"]

    @property
    def name(self):
        return [e["Value"] for e in self._data["Tags"] if e["Key"] == "Name"][0]

    @property
    def state(self):
        return self._data["State"]["Name"]

    @property
    def private_ip(self):
        return self._data["NetworkInterfaces"][0]["PrivateIpAddress"]


def describe_instances():
    client = boto3.client("ec2")
    instances = client.describe_instances()

    result = []
    for e in chain.from_iterable(r["Instances"] for r in instances["Reservations"]):
        result.append(Instance(e))
    return result


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
@click.option(
    "-s", "--state", default="", help="Filter instances by state.", metavar="STATE"
)
def list_ec2_instances(name, state):
    """List ec2 instances."""
    instances = describe_instances()
    for i in instances:
        if (
            name.lower() in i.name.lower()
            and state.lower() in i.state.lower()
        ):
            click.echo(
                "\t".join(
                    [
                        i.instance_id,
                        i.name,
                        colorize_state(i.state),
                        i.private_ip,
                    ]
                )
            )


async def start_instance(instance_id):
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)
    if instance.state["Name"] != "stopped":
        click.echo(f"Oops, ec2 instance({instance_id}) is not stopped.", err=True)
        return
    instance.start()
    click.echo(f"ec2 instance({instance_id}) is now starting...", err=True)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, instance.wait_until_running)
    click.echo(f"ec2 instance({instance_id}) has started🚀", err=True)


@cli.command("start")
@click.argument("instance_ids", nargs=-1, metavar="[INSTANCE_ID ...]")
def start_ec2_instances(instance_ids):
    """Start ec2 instances."""
    if not sys.stdin.isatty():
        # stdin from pipe
        instance_ids = click.get_text_stream("stdin").read().strip().split()

    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(*[start_instance(i) for i in instance_ids])
    loop.run_until_complete(tasks)
    loop.close()


async def stop_instance(instance_id):
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(instance_id)
    if instance.state["Name"] != "running":
        click.echo(f"Oops, ec2 instance({instance_id}) is not running.", err=True)
        return
    instance.stop()
    click.echo(f"ec2 instance({instance_id}) is now stopping...", err=True)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, instance.wait_until_stopped)
    click.echo(f"ec2 instance({instance_id}) has stopped💤", err=True)


@cli.command("stop")
@click.argument("instance_ids", nargs=-1, metavar="[INSTANCE_ID ...]")
def stop_ec2_instances(instance_ids):
    """Stop ec2 instances."""
    if not sys.stdin.isatty():
        # stdin from pipe
        instance_ids = click.get_text_stream("stdin").read().strip().split()

    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(*[stop_instance(i) for i in instance_ids])
    loop.run_until_complete(tasks)
    loop.close()


if __name__ == "__main__":
    cli()
