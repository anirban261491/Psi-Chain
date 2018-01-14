import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request


class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        lookup_table = {}
        self.new_block(lookup_table, previous_hash=1)

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            #print(f'{last_block}')
            #print(f'{block}')
            #print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                print('previous')
                return False

            # Check that the Proof of Work is correct
            if block['hash'] != self.hash(block):
                print('current')
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, lookup_table, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        if(not self.current_transactions and self.chain):
            return False

        for i in self.current_transactions:
            if (i['License'] in lookup_table):
                lookup_table[i['License']].append(i['Location'])
            else:
                lookup_table[i['License']] = list()
                lookup_table[i['License']].append(i['Location'])

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'previous_hash': previous_hash,
            'lookup_table': lookup_table
        }

        if(previous_hash is 1):
            block.pop('timestamp', {})
            block['nonce'] = 1
            block['hash'] = self.hash(block)
        else:
            nonce = self.proof_of_work(block)

        # Reset the current list of transactions
        self.current_transactions = []

        self.getChain().append(block)
        return block

    def new_transaction(self, License, Location):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """

        self.current_transactions.append({
            'License': License,
            'Location': Location,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        if(self.chain):
            return self.chain[-1]
        else:
            return {}

    def getChain(self):
        return self.chain

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        current_block = block.copy()
        current_block.pop('hash', None)
        block_string = json.dumps(current_block, sort_keys = True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def removeLookup(self, block):
        if(block['previous_hash'] is 1):
            return {}
        lookup_table = block.pop('lookup_table', {})
        block.pop('hash', {})
        nonce = self.proof_of_work(block)
        return lookup_table

    def proof_of_work(self, block):

        nonce = 0
        (success, guess_hash) =  self.valid_proof(block, nonce)
        while success is False:
            nonce += 1
            (success, guess_hash) =  self.valid_proof(block, nonce) 

        block['hash'] = guess_hash
        return nonce

    @staticmethod
    def valid_proof(block, nonce):

        block['nonce'] = nonce

        guess = json.dumps(block, sort_keys = True).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return (guess_hash[:4] == "0000",guess_hash)


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

import threading
#@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    print("Mining")

    last_block = blockchain.last_block

    if(not last_block or not blockchain.current_transactions):
        threading.Timer(3, mine).start()
        return

    lookup_table = blockchain.removeLookup(last_block)

    previous_hash = last_block['hash']

    block = blockchain.new_block(lookup_table, previous_hash)

    if(not block):
        threading.Timer(3, mine).start()
        return

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'hash': block['hash'],
        'previous_hash': block['previous_hash'],
    }

    threading.Timer(3, mine).start()

mine()

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['License', 'Location']
    if not all(k in values for k in required):
        response = {'message': f'Error. Missing values'}
        return jsonify(response), 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['License'], values['Location'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

def consensus():
    print("Consensus called")
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    threading.Timer(10, consensus).start()

consensus()

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)

