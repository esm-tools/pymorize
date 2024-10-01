import subprocess

import rich_click as click


@click.command()
@click.option("--local-port", default=8787, help="Local port to forward from")
@click.option("--remote-port", default=8787, help="Remote port to forward to")
@click.option("--gateway", default="levante2.dkrz.de", help="Gateway server hostname")
@click.option("--compute-node", required=True, help="Compute node hostname")
@click.option("--username", required=True, help="Username for SSH connections")
def ssh_tunnel_cli(local_port, remote_port, gateway, compute_node, username):
    """
    Create an SSH tunnel to access a Dask dashboard on a remote compute node.

    This script sets up an SSH tunnel to access a Dask dashboard running
    on a remote compute node, routed through a gateway server.
    """
    ssh_command = f"ssh -nNT -L {local_port}:{compute_node}:{remote_port} -L 4200:{compute_node}:4200 {username}@{gateway}"

    click.echo(f"Creating SSH tunnel via: {ssh_command}")
    click.echo(
        f"Port forwarding: localhost:{local_port} -> {gateway}:{remote_port} -> {compute_node}:{remote_port}"
    )
    click.echo(f"Dashboard will be accessible at http://localhost:{local_port}/status")
    click.echo("Press Ctrl+C to close the tunnel")

    try:
        # Run the SSH command
        subprocess.run(ssh_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"An error occurred while creating the SSH tunnel: {e}")
    except KeyboardInterrupt:
        click.echo("SSH tunnel closed.")


if __name__ == "__main__":
    ssh_tunnel_cli()
