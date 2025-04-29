"""
Skill Repository for Knowledge Graph
This module provides skill-related database operations.
"""

from src.backend.repositories.base.repository import BaseRepository
import uuid

class SkillRepository(BaseRepository):
    """Repository for skill-related operations in the knowledge graph."""
    
    def add_skill(self, skill_data):
        """Add a skill node to the graph.
        
        Args:
            skill_data: Dictionary containing skill information
            
        Returns:
            skill_id of the created skill
        """
        # Generate skill_id if not provided
        if "skill_id" not in skill_data:
            skill_data["skill_id"] = f"skill_{str(uuid.uuid4())[:8]}"
            
        query = """
            MERGE (s:Skill {skill_id: $skill_id})
            SET s.name = $name,
                s.category = $category,
                s.domain = $domain,
                s.description = $description
            RETURN s.skill_id as skill_id
        """
        
        parameters = {
            "skill_id": skill_data["skill_id"],
            "name": skill_data["name"],
            "category": skill_data.get("category", ""),
            "domain": skill_data.get("domain", ""),
            "description": skill_data.get("description", "")
        }
        
        self.execute_write_query(query, parameters)
        return skill_data["skill_id"]
    
    def add_skill_relationship(self, source_id, target_id, rel_type, weight=1.0):
        """Add a relationship between two skill nodes.
        
        Args:
            source_id: ID of the source skill
            target_id: ID of the target skill
            rel_type: Type of relationship (e.g., 'related_to', 'complementary_to')
            weight: Relationship weight/strength or dictionary of properties
            
        Returns:
            True if successful
        """
        # Handle both weight as a number and as a properties dictionary
        properties = {"weight": weight} if isinstance(weight, (int, float)) else weight
        
        # Convert properties to a Cypher parameter string
        props_string = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        
        query = f"""
            MATCH (s1:Skill {{skill_id: $source_id}})
            MATCH (s2:Skill {{skill_id: $target_id}})
            MERGE (s1)-[r:`{rel_type}` {{{props_string}}}]->(s2)
        """
        
        parameters = {
            "source_id": source_id, 
            "target_id": target_id
        }
        parameters.update(properties)
        
        self.execute_write_query(query, parameters)
        return True
    
    def get_skill(self, skill_id):
        """Get a skill by ID.
        
        Args:
            skill_id: ID of the skill
            
        Returns:
            Skill data as dictionary or None if not found
        """
        query = """
            MATCH (s:Skill {skill_id: $skill_id})
            RETURN s.skill_id as skill_id, s.name as name, s.category as category, 
                   s.domain as domain, s.description as description
        """
        
        results = self.execute_read_query(query, {"skill_id": skill_id})
        if not results:
            return None
            
        return results[0]
    
    def get_skills_by_category(self, category):
        """Get skills by category.
        
        Args:
            category: Skill category
            
        Returns:
            List of skills in the specified category
        """
        query = """
            MATCH (s:Skill)
            WHERE s.category = $category
            RETURN s.skill_id as skill_id, s.name as name, s.category as category, 
                   s.domain as domain, s.description as description
            ORDER BY s.name
        """
        
        return self.execute_read_query(query, {"category": category})
    
    def get_all_skills(self):
        """Get all skills.
        
        Returns:
            List of all skills
        """
        query = """
            MATCH (s:Skill)
            RETURN s.skill_id as skill_id, s.name as name, s.category as category, 
                   s.domain as domain, s.description as description
            ORDER BY s.name
        """
        
        return self.execute_read_query(query)
    
    def find_skills(self, filters=None, limit=50, offset=0):
        """Find skills matching specified filters.
        
        Args:
            filters: Dictionary containing filter criteria
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List of skills matching the filters
        """
        # Prepare WHERE clauses based on filters
        where_clauses = []
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if filters:
            # Handle name filter
            if 'name' in filters and filters['name']:
                where_clauses.append("toLower(s.name) CONTAINS toLower($name)")
                params['name'] = filters['name']
            
            # Handle category filter
            if 'category' in filters and filters['category']:
                where_clauses.append("s.category = $category")
                params['category'] = filters['category']
            
            # Handle domain filter
            if 'domain' in filters and filters['domain']:
                where_clauses.append("s.domain = $domain")
                params['domain'] = filters['domain']
        
        # Build query
        query = """
            MATCH (s:Skill)
        """
        
        # Add WHERE clause if there are filters
        if where_clauses:
            query += "WHERE " + " AND ".join(where_clauses)
        
        # Add return statement
        query += """
            RETURN s.skill_id as skill_id, s.name as name, s.category as category, 
                   s.domain as domain, s.description as description
            ORDER BY s.name
            SKIP $offset
            LIMIT $limit
        """
        
        return self.execute_read_query(query, params)
    
    def get_related_skills(self, skill_id, relationship_type=None):
        """Get skills related to a given skill.
        
        Args:
            skill_id: ID of the skill
            relationship_type: Optional specific relationship type to filter by
            
        Returns:
            List of related skills with relationship information
        """
        if relationship_type:
            query = f"""
                MATCH (s1:Skill {{skill_id: $skill_id}})-[r:`{relationship_type}`]-(s2:Skill)
                RETURN s2.skill_id as skill_id, s2.name as name, 
                       s2.category as category, type(r) as relationship_type,
                       r.weight as weight
            """
        else:
            query = """
                MATCH (s1:Skill {skill_id: $skill_id})-[r]-(s2:Skill)
                RETURN s2.skill_id as skill_id, s2.name as name, 
                       s2.category as category, type(r) as relationship_type,
                       r.weight as weight
            """
        
        return self.execute_read_query(query, {"skill_id": skill_id})
    
    def get_skill_path(self, start_skill_id, end_skill_id, max_depth=3):
        """Find a learning path between two skills.
        
        Args:
            start_skill_id: Starting skill ID
            end_skill_id: Target skill ID
            max_depth: Maximum path length
            
        Returns:
            Dictionary with path information or None if no path exists
        """
        # Neo4j doesn't support parameters in path length specifications
        # Convert max_depth to an integer and include it directly in the query
        max_depth_int = int(max_depth)
        relationship_pattern = f"[:RELATED_TO|REQUIRES|COMPLEMENTARY_TO*1..{max_depth_int}]"
        
        query = f"""
            MATCH path = shortestPath((s1:Skill {{skill_id: $start_skill_id}})-{relationship_pattern}->(s2:Skill {{skill_id: $end_skill_id}}))
            WITH [node in nodes(path) | node.skill_id] AS skill_ids,
                 [node in nodes(path) | node.name] AS skill_names,
                 [rel in relationships(path) | type(rel)] AS relationship_types
            RETURN skill_ids, skill_names, relationship_types
        """
        
        results = self.execute_read_query(query, {
            "start_skill_id": start_skill_id, 
            "end_skill_id": end_skill_id
        })
        
        if not results:
            return None
            
        return {
            "skill_ids": results[0]["skill_ids"],
            "skill_names": results[0]["skill_names"],
            "relationship_types": results[0]["relationship_types"]
        }
    
    def recommend_skills(self, resume_id, limit=5):
        """Recommend skills for a candidate to learn based on job market demands.
        
        Args:
            resume_id: ID of the candidate
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended skills with rationale
        """
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})-[:HAS_CORE_SKILL]->(s1:Skill)
            MATCH (s1)-[:RELATED_TO|COMPLEMENTARY_TO]->(s2:Skill)
            WHERE NOT (c)-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(s2)
            WITH s2, count(s1) as relevance
            MATCH (j:Job)-[:REQUIRES_PRIMARY]->(s2)
            RETURN s2.skill_id as skill_id, s2.name as name, count(j) as job_demand, 
                   relevance, count(j) * relevance as score
            ORDER BY score DESC
            LIMIT $limit
        """
        
        return self.execute_read_query(query, {"resume_id": resume_id, "limit": limit})
    
    def recommend_skills_for_job(self, resume_id, job_id, limit=5):
        """Recommend skills for a candidate to learn for a specific job.
        
        Args:
            resume_id: ID of the candidate
            job_id: ID of the job
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended skills with learning value
        """
        query = """
            MATCH (j:Job {job_id: $job_id})-[r:REQUIRES_PRIMARY]->(s:Skill)
            WHERE NOT (s)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(:Candidate {resume_id: $resume_id})
            
            // Find candidate's existing skills that are related to the missing skills
            OPTIONAL MATCH (c:Candidate {resume_id: $resume_id})-[:HAS_CORE_SKILL]->(cs:Skill)
                             -[:RELATED_TO|REQUIRES|COMPLEMENTARY_TO]->(s)
            
            RETURN s.skill_id as skill_id, s.name as name, 
                   r.importance as job_importance,
                   count(cs) as relevance_to_existing_skills,
                   r.importance * (1 + count(cs)/3) as learning_value
            ORDER BY learning_value DESC
            LIMIT $limit
        """
        
        return self.execute_read_query(query, {
            "resume_id": resume_id, 
            "job_id": job_id, 
            "limit": limit
        })
    
    def find_skill_by_name(self, skill_name):
        """Find a skill by name (case insensitive).
        
        Args:
            skill_name: Name of the skill to find
            
        Returns:
            Skill data as dictionary or None if not found
        """
        query = """
            MATCH (s:Skill)
            WHERE toLower(s.name) = toLower($skill_name)
            RETURN s.skill_id as skill_id, s.name as name, s.category as category, 
                   s.domain as domain, s.description as description
        """
        
        results = self.execute_read_query(query, {"skill_name": skill_name})
        if not results:
            return None
            
        return results[0]
        
    def _extract_skill_details(self, cypher_response, required_fields, optional_fields=None):
        """Extract skill details from Cypher query response, filtering fields.
        
        Args:
            cypher_response: List of dictionaries from Neo4j query
            required_fields: List of fields that must be present
            optional_fields: List of optional fields to include if present
            
        Returns:
            List of dictionaries with filtered skill details
        """
        if optional_fields is None:
            optional_fields = []
            
        result = []
        
        for record in cypher_response:
            # Check if all required fields are present
            if all(field in record for field in required_fields):
                skill_data = {}
                
                # Add required fields
                for field in required_fields:
                    skill_data[field] = record[field]
                    
                # Add optional fields if present
                for field in optional_fields:
                    if field in record:
                        skill_data[field] = record[field]
                        
                result.append(skill_data)
                
        return result

    def get_skill_graph(self, skill_id):
        """Get graph data for a skill and its relationships.
        
        Args:
            skill_id: ID of the skill to visualize
            
        Returns:
            Dictionary with nodes and edges for graph visualization
        """
        # Get the central skill
        query_central = """
            MATCH (s:Skill {skill_id: $skill_id})
            RETURN s.skill_id as id, s.name as name, s.category as category, 'skill' as type
        """
        
        nodes = self.execute_read_query(query_central, {"skill_id": skill_id})
        if not nodes:
            print(f"Central skill not found: {skill_id}")
            return {"nodes": [], "edges": []}
            
        # Get related skills - direct connections only, using a more robust query
        query_related = """
            MATCH (s:Skill {skill_id: $skill_id})-[r]-(related:Skill)
            RETURN related.skill_id as id, 
                   related.name as name, 
                   related.category as category,
                   'skill' as type,
                   s.skill_id as source,
                   related.skill_id as target,
                   type(r) as relationship
        """
        
        related_results = self.execute_read_query(query_related, {"skill_id": skill_id})
        
        # Process results
        nodes_dict = {nodes[0]['id']: nodes[0]}  # Add the central node
        edges = []
        
        for record in related_results:
            # Only process nodes with valid IDs
            if record.get('id') is not None:
                # Add node if not already present
                if record['id'] not in nodes_dict:
                    nodes_dict[record['id']] = {
                        'id': record['id'],
                        'name': record.get('name', 'Unknown'),
                        'category': record.get('category', ''),
                        'type': record.get('type', 'skill')
                    }
                
                # Only add edges with valid source and target
                if record.get('source') is not None and record.get('target') is not None:
                    edges.append({
                        'source': record['source'],
                        'target': record['target'],
                        'relationship': record.get('relationship', 'related_to')
                    })
        
        print(f"Built skill graph for {skill_id} with {len(nodes_dict)} nodes and {len(edges)} edges")
        return {
            'nodes': list(nodes_dict.values()),
            'edges': edges
        }
    
    def get_skills_network(self, limit=100):
        """Get network of skills and relationships for visualization.
        
        Args:
            limit: Maximum number of skills to include
            
        Returns:
            Dictionary with nodes and edges for network visualization
        """
        # Get skills with a simpler query
        query_nodes = """
            MATCH (s:Skill)
            RETURN s.skill_id as id, s.name as name, s.category as category, 'skill' as type
            LIMIT $limit
        """
        
        nodes = self.execute_read_query(query_nodes, {"limit": limit})
        
        # Handle empty results
        if not nodes:
            return {"nodes": [], "edges": []}
        
        # Create a dictionary of nodes for fast lookups
        nodes_dict = {node['id']: node for node in nodes if node.get('id') is not None}
        skill_ids = list(nodes_dict.keys())
        
        # Skip relationships if no nodes found
        if not skill_ids:
            return {"nodes": [], "edges": []}
            
        # Get all relationships between skills directly without filtering by skill_ids
        # This is safer as it avoids passing large parameter lists
        query_edges = """
            MATCH (s1:Skill)-[r]-(s2:Skill)
            WHERE s1.skill_id IN $skill_ids AND s2.skill_id IN $skill_ids
            RETURN s1.skill_id as source, s2.skill_id as target, type(r) as relationship
            LIMIT 1000
        """
        
        edges_results = self.execute_read_query(query_edges, {"skill_ids": skill_ids})
        
        # Process edges
        edges = []
        edge_keys = set()
        
        for record in edges_results:
            source = record.get('source')
            target = record.get('target')
            rel_type = record.get('relationship')
            
            # Skip invalid relationships
            if not source or not target or not rel_type:
                continue
                
            # Create a unique key for each relationship type between two nodes
            key = f"{min(source, target)}-{max(source, target)}-{rel_type}"
            
            if key not in edge_keys:
                edges.append({
                    'source': source,
                    'target': target,
                    'relationship': rel_type
                })
                edge_keys.add(key)
        
        print(f"Built graph with {len(nodes_dict)} nodes and {len(edges)} edges")
        return {
            'nodes': list(nodes_dict.values()),
            'edges': edges
        } 