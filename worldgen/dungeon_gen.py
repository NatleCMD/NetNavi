"""
Dungeon Generator - Creates node-based dungeon maps.
"""

import random
import math


class DungeonGenerator:
    """Generates node-graph dungeons from seeds."""
    
    NODE_TYPES = ["empty", "encounter", "cache", "heal", "boss", "exit", "start"]
    
    def generate(self, seed: int, node_count: int = 8) -> dict:
        """Generate a dungeon layout."""
        rng = random.Random(seed)
        
        nodes = []
        
        # Layout parameters
        width = 280
        height = 200
        margin = 40
        
        # Generate node positions (spread out)
        positions = self._generate_positions(rng, node_count, width, height, margin)
        
        # Create nodes with types
        for i, (x, y) in enumerate(positions):
            if i == 0:
                node_type = "start"
            elif i == len(positions) - 1:
                node_type = "boss"
            else:
                node_type = self._pick_node_type(rng, i, len(positions))
            
            node = {
                "x": x,
                "y": y,
                "type": node_type,
                "connections": [],
                "enemy": None,
                "loot": None,
            }
            
            # Add enemy data for encounter nodes
            if node_type in ["encounter", "boss"]:
                node["enemy"] = self._generate_enemy(rng, node_type == "boss")
            
            # Add loot for cache nodes
            if node_type == "cache":
                node["loot"] = {"zenny": rng.randint(20, 80)}
            
            nodes.append(node)
        
        # Connect nodes (create graph)
        self._connect_nodes(nodes, rng)
        
        # Ensure path from start to boss exists
        self._ensure_connectivity(nodes)
        
        return {
            "nodes": nodes,
            "seed": seed,
        }
    
    def _generate_positions(self, rng, count, width, height, margin):
        """Generate spread-out node positions."""
        positions = []
        
        # Start node at left
        positions.append((margin, height // 2))
        
        # Distribute other nodes
        for i in range(1, count - 1):
            # Spread horizontally with some vertical variance
            x = margin + int((width - 2 * margin) * (i / (count - 1)))
            y = margin + rng.randint(0, height - 2 * margin)
            
            # Avoid overlap
            for px, py in positions:
                if abs(x - px) < 30 and abs(y - py) < 30:
                    y = (y + 40) % (height - margin)
            
            positions.append((x, y))
        
        # Boss at right
        positions.append((width - margin, height // 2))
        
        return positions
    
    def _pick_node_type(self, rng, index, total):
        """Pick node type based on position and randomness."""
        weights = {
            "empty": 15,
            "encounter": 40,
            "cache": 20,
            "heal": 10,
        }
        
        # Add exit near the end
        if index > total * 0.7:
            weights["exit"] = 15
        
        types = list(weights.keys())
        probs = list(weights.values())
        total_weight = sum(probs)
        probs = [p / total_weight for p in probs]
        
        return rng.choices(types, probs)[0]
    
    def _generate_enemy(self, rng, is_boss: bool) -> dict:
        """Generate enemy data."""
        if is_boss:
            names = ["OmegaVirus", "NetDragon", "MegaMett", "ShadowNavi"]
            return {
                "name": rng.choice(names),
                "hp": rng.randint(80, 120),
                "attack": rng.randint(15, 25),
                "defense": rng.randint(3, 8),
                "is_boss": True,
            }
        else:
            names = ["Mettaur", "Spikey", "Bunny", "Fishy", "Canodumb"]
            return {
                "name": rng.choice(names),
                "hp": rng.randint(25, 50),
                "attack": rng.randint(8, 15),
                "defense": rng.randint(0, 4),
                "is_boss": False,
            }
    
    def _connect_nodes(self, nodes, rng):
        """Create connections between nearby nodes."""
        for i, node in enumerate(nodes):
            # Find nearby nodes
            distances = []
            for j, other in enumerate(nodes):
                if i != j:
                    dx = node["x"] - other["x"]
                    dy = node["y"] - other["y"]
                    dist = math.sqrt(dx * dx + dy * dy)
                    distances.append((dist, j))
            
            # Connect to 2-3 nearest
            distances.sort()
            connect_count = rng.randint(2, 3)
            for dist, j in distances[:connect_count]:
                if j not in node["connections"]:
                    node["connections"].append(j)
                if i not in nodes[j]["connections"]:
                    nodes[j]["connections"].append(i)
    
    def _ensure_connectivity(self, nodes):
        """Make sure all nodes are reachable from start."""
        visited = {0}
        queue = [0]
        
        while queue:
            current = queue.pop(0)
            for conn in nodes[current]["connections"]:
                if conn not in visited:
                    visited.add(conn)
                    queue.append(conn)
        
        # Connect any unreachable nodes
        for i in range(len(nodes)):
            if i not in visited:
                # Connect to nearest visited node
                best_dist = float("inf")
                best_j = 0
                for j in visited:
                    dx = nodes[i]["x"] - nodes[j]["x"]
                    dy = nodes[i]["y"] - nodes[j]["y"]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < best_dist:
                        best_dist = dist
                        best_j = j
                
                nodes[i]["connections"].append(best_j)
                nodes[best_j]["connections"].append(i)
                visited.add(i)
