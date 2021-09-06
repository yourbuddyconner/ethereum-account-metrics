from web3 import Web3
from prometheus_client import start_http_server, Counter, Gauge
import click
import time
import signal
import logging
import sys

@click.command()
@click.option('--rpc', default=["https://alfajores-forno.celo-testnet.org"], help='RPC Endpoint to query for data', multiple=True)
@click.option('--address', help='An Ethereum address to monitor', multiple=True)
@click.option('--metrics-port', default=9090, help="Port to bind metrics server to.")
@click.option('--pause-duration', default=30, help="Number of seconds to sleep between polling.")
def account_metrics(rpc, address, metrics_port, pause_duration):
    """Simple program that polls one or more ethereum accounts and reports metrics on them."""
    # Set up prometheus metrics 
    metrics = {
        "wallet_balance": Gauge("ethereum_wallet_balance", "ETH Wallet Balance", ["address", "rpc"]),
        "transaction_count": Gauge("ethereum_transaction_count", "ETH Wallet Balance", ["address", "rpc"]),
        "block_number": Gauge("ethereum_block_height", "Block Height", ["rpc"])
    }

    # Set up logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # run metrics endpoint
    start_http_server(metrics_port)
    logging.info(f"Running Prometheus endpoint on port {metrics_port}")

    # register for sigint 
    #signal.signal(signal.SIGINT, signal_handler)

    assert len(rpc) > 0, "Must pass at least one RPC"
    assert len(address) > 0, "Must pass at least one address"

    logging.info("Executing event loop, Ctrl+C to exit.")
    # main event loop
    while True:
        # for each rpc
        for endpoint in rpc:
            w3 = Web3(Web3.HTTPProvider(endpoint))

            # Fetch block height
            block_height = w3.eth.get_block_number()
            metrics["block_number"].labels(rpc=endpoint).set(block_height)

            # for each account
            for account in address:
                logging.info(f"Fetching metrics for {account} via {endpoint}")
                # fetch balance
                wallet_wei = w3.eth.get_balance(account)
                wallet_eth = w3.fromWei(wallet_wei, "ether")
                # fetch tx count
                tx_count = w3.eth.get_transaction_count(account)
                # report metrics 
                metrics["wallet_balance"].labels(address=account, rpc=endpoint).set(wallet_eth)
                metrics["transaction_count"].labels(address=account, rpc=endpoint).set(tx_count)
        logging.info(f"Sleeping for {pause_duration} seconds.")
        time.sleep(pause_duration)
    
def signal_handler(signum, frame):
    print('Exiting...')
    sys.exit(0)

if __name__ == '__main__':
    account_metrics(auto_envvar_prefix="METRICS")
