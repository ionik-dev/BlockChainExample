import hashlib
import json

from textwrap import dedent
from time import time
from urllib.parse import urlparse 
import requests


class Blockchain(object):

    def __init__(self):
        """
        Initialize blockchain
        """
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        self.new_block(previous_hash=1, proof=100)


    def new_block(self, proof, previous_hash=None):
        """
        Create a new block in chain

        :parameter proof: <int> proof created by ProofOfWork (PoW)
        :parameter previous_hash: (optional) <str>Hash of previous block
        :return: <dict> New Block
        """
        
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.current_transactions = []

        self.chain.append(block)
        return block


    def new_transaction(self, sender, recipient, amount):
        """
        Create new transaction

        :parameter sender: <str> Sender address
        :parameter recipient: <str> Recipient address
        :parameter amount: <int> Payment amount
        :return: <int> Block index which will contain a transaction
        """
        
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1


    def proof_of_work(self, last_proof):
        """
        Simple algo for Proof of Work:
          - Find a p', which should has a hash(pp') with four leading zeros like 0000.....
 
        :parameter: last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof


    def register_node(self, address):
        """
        Add new node to the node-list

        :parameter address: <str> Node address, ex. 'http://192.168.10.1:4000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


    def valid_chain(self, chain):
        """
        Check that given blockchain pass validation

        :parameter chain: <list> Blockchain
        :return: <bool> True if validation passed, False instead
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}') 
            print(f'{block}')
            print("\n-----------\n")
            # Check, that block hash is valid
            if block['previous_hash'] != self.hash(last_block):
                return False
 
            # Check, that PoW is valid
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
 
  
            last_block = block
  
            current_index += 1
 
        return True


    def resolve_conflicts(self):
        """
        Consensus algorithm, replace chain with the longest one

        :return: <bool> True if chain has been replaced, False instead
        """

        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        # retrive chains from all nodes
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
 
                # Check for max length and validity
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
 
        # replace if foung longest one and it also valid
        if new_chain:
            self.chain = new_chain
            return True
  
        return False

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Check Proof: If hash(last_proof, proof) containing a 4 leading zero?
 
        :parameter last_proof: <int> previous Proof
        :parameter proof: <int> current Proof
        :return:
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'


    @staticmethod
    def hash(block):
        """
        Generate SHA-256 block hash

        :parameter block: <dict> Block
        :return: <str>
        """
        
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


    @property
    def last_block(self):
        return self.chain[-1]

