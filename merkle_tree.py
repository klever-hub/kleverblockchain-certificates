#!/usr/bin/env python3
import hashlib
import json
from typing import List, Dict, Optional, Tuple

class MerkleTree:
    """Implementation of a Merkle tree for certificate metadata"""
    
    def __init__(self):
        self.leaves = []
        self.tree = []
        self.proofs = {}
    
    def hash_leaf(self, data: str) -> str:
        """Hash a leaf node with double SHA256"""
        # Double hash to prevent length extension attacks
        first_hash = hashlib.sha256(data.encode('utf-8')).digest()
        return hashlib.sha256(first_hash).hexdigest()
    
    def hash_pair(self, left: str, right: str) -> str:
        """Hash two nodes together"""
        # Sort to ensure consistent ordering
        if left > right:
            left, right = right, left
        combined = left + right
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def add_leaf(self, field_name: str, field_value: str):
        """Add a field to the tree as a leaf"""
        # Create a deterministic string representation
        leaf_data = f"{field_name}:{field_value}"
        leaf_hash = self.hash_leaf(leaf_data)
        self.leaves.append({
            'field': field_name,
            'value': field_value,
            'hash': leaf_hash
        })
    
    def build_tree(self):
        """Build the Merkle tree from leaves"""
        if not self.leaves:
            return None
        
        # Initialize tree with leaf hashes
        current_level = [leaf['hash'] for leaf in self.leaves]
        self.tree = [current_level[:]]
        
        # Build tree level by level
        while len(current_level) > 1:
            next_level = []
            
            # Process pairs
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    # Hash pair
                    parent_hash = self.hash_pair(current_level[i], current_level[i + 1])
                else:
                    # Odd number of nodes - promote the last one
                    parent_hash = current_level[i]
                
                next_level.append(parent_hash)
            
            self.tree.append(next_level[:])
            current_level = next_level
        
        # Generate proofs for each leaf
        self._generate_proofs()
        
        return current_level[0] if current_level else None
    
    def _generate_proofs(self):
        """Generate Merkle proofs for each leaf"""
        if not self.tree or not self.leaves:
            return
        
        for leaf_idx, leaf in enumerate(self.leaves):
            proof = []
            current_idx = leaf_idx
            
            # Traverse up the tree
            for level_idx in range(len(self.tree) - 1):
                level = self.tree[level_idx]
                
                # Find sibling
                if current_idx % 2 == 0:
                    # Right sibling
                    sibling_idx = current_idx + 1
                    position = 'right'
                else:
                    # Left sibling
                    sibling_idx = current_idx - 1
                    position = 'left'
                
                # Add sibling to proof if it exists
                if sibling_idx < len(level):
                    proof.append({
                        'hash': level[sibling_idx],
                        'position': position
                    })
                
                # Move to parent index
                current_idx = current_idx // 2
            
            self.proofs[leaf['field']] = proof
    
    def get_root(self) -> Optional[str]:
        """Get the Merkle root"""
        if self.tree and self.tree[-1]:
            return self.tree[-1][0]
        return None
    
    def get_proof(self, field_name: str) -> Optional[List[Dict]]:
        """Get the Merkle proof for a specific field"""
        return self.proofs.get(field_name)
    
    def verify_proof(self, field_name: str, field_value: str, root_hash: str, proof: List[Dict]) -> bool:
        """Verify a Merkle proof"""
        # Calculate leaf hash
        leaf_data = f"{field_name}:{field_value}"
        current_hash = self.hash_leaf(leaf_data)
        
        # Apply proof
        for proof_element in proof:
            sibling_hash = proof_element['hash']
            position = proof_element['position']
            
            if position == 'right':
                current_hash = self.hash_pair(current_hash, sibling_hash)
            else:
                current_hash = self.hash_pair(sibling_hash, current_hash)
        
        # Compare with root
        return current_hash == root_hash


def create_certificate_merkle_tree(certificate_data: Dict) -> Tuple[str, Dict[str, List[Dict]]]:
    """
    Create a Merkle tree for certificate data
    Returns: (root_hash, proofs_dict)
    """
    tree = MerkleTree()
    
    # Add fields to the tree
    # Note: We're creating a tree of all metadata fields
    fields_to_include = [
        ('name', certificate_data['name']),
        ('course', certificate_data['course']),
        ('course_load', certificate_data.get('course_load', '')),
        ('location', certificate_data['location']),
        ('date', certificate_data['date']),
        ('instructor', certificate_data['instructor']),
        ('instructor_title', certificate_data['instructor_title']),
        ('issuer', certificate_data.get('issuer', '')),
        ('nft_id', certificate_data['nft_id']),
        ('pdf_hash', certificate_data['pdf_hash'])
    ]
    
    for field_name, field_value in fields_to_include:
        tree.add_leaf(field_name, field_value)
    
    # Build tree and get root
    root_hash = tree.build_tree()
    
    # Get all proofs
    proofs = {}
    for field_name, _ in fields_to_include:
        proof = tree.get_proof(field_name)
        if proof:
            proofs[f"{field_name}Proof"] = proof
    
    return root_hash, proofs


def verify_certificate_field(field_name: str, field_value: str, root_hash: str, proof: List[Dict]) -> bool:
    """
    Verify a single field against the Merkle root
    """
    tree = MerkleTree()
    return tree.verify_proof(field_name, field_value, root_hash, proof)