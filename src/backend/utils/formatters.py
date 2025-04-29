"""
Formatter Utilities

This module provides functions for formatting data for API responses.
"""

def format_match_results(matches):
    """Format match results for frontend display with consistent scoring and skill data.
    
    Args:
        matches: List of match results to format
        
    Returns:
        list: Formatted match results
    """
    formatted_matches = []
    
    for match in matches:
        formatted_match = dict(match)  # Create a copy to avoid modifying the original
        
        # Ensure match_percentage exists
        if 'match_percentage' not in formatted_match:
            if 'hybrid_score' in formatted_match:
                # Scale hybrid_score (0-1) to percentage (0-100)
                formatted_match['match_percentage'] = _score_to_percentage(formatted_match['hybrid_score'])
            elif 'matchScore' in formatted_match:
                # Convert match score to percentage
                formatted_match['match_percentage'] = min(int(formatted_match['matchScore'] * 10), 100)
            else:
                formatted_match['match_percentage'] = 0
        
        # Round match_percentage to integer if it's a float
        if isinstance(formatted_match['match_percentage'], float):
            formatted_match['match_percentage'] = int(round(formatted_match['match_percentage']))
        
        # Ensure graph_percentage and text_percentage exist
        if 'graph_percentage' not in formatted_match:
            formatted_match['graph_percentage'] = formatted_match['match_percentage']
        if 'text_percentage' not in formatted_match:
            formatted_match['text_percentage'] = formatted_match['match_percentage']
            
        # Format matching skills for frontend display
        if 'primary_matching_skills' in formatted_match:
            # Only use primary_matching_skills for matching_skills
            formatted_match['matching_skills'] = [s for s in formatted_match['primary_matching_skills'] if s and s.get('skill_id') is not None]
            
        # Keep secondary_matching_skills separate for the frontend
        if 'secondary_matching_skills' in formatted_match:
            # Filter out null skills
            formatted_match['secondary_matching_skills'] = [s for s in formatted_match['secondary_matching_skills'] 
                                                if s and s.get('skill_id') is not None]
            
            # Remove duplicate skills that are already in primary
            if 'matching_skills' in formatted_match:
                primary_skill_ids = {s.get('skill_id') for s in formatted_match.get('matching_skills', [])}
                formatted_match['secondary_matching_skills'] = [s for s in formatted_match['secondary_matching_skills'] 
                                                     if s.get('skill_id') not in primary_skill_ids]
        
        # Add placeholder values for frontend compatibility
        if 'matching_skills' not in formatted_match:
            formatted_match['matching_skills'] = []
        if 'secondary_matching_skills' not in formatted_match:
            formatted_match['secondary_matching_skills'] = []
        if 'missing_skills' not in formatted_match:
            formatted_match['missing_skills'] = []
        if 'exceeding_skills' not in formatted_match:
            formatted_match['exceeding_skills'] = []
        
        # Round scores for display
        for score_field in ['skillScore', 'locationScore', 'semanticScore', 'totalScore', 'match_percentage', 'graph_percentage', 'text_percentage']:
            if score_field in formatted_match:
                try:
                    formatted_match[score_field] = round(float(formatted_match[score_field]), 1)
                except (ValueError, TypeError):
                    formatted_match[score_field] = 0.0
                
        # Remove raw skills arrays to clean up response
        if 'primary_matching_skills' in formatted_match:
            del formatted_match['primary_matching_skills']
            
        formatted_matches.append(formatted_match)
        
    return formatted_matches

def _score_to_percentage(score):
    """Convert normalized score to percentage with distribution adjustment.
    
    This applies a modified curve to spread scores appropriately across ranges:
    - Excellent matches (85-100% range) - only for candidates with almost all primary skills
    - High matches (70-85% range)
    - Medium matches (60-70% range)
    - Low matches (<60% range)
    
    Args:
        score: Normalized score between 0 and 1
        
    Returns:
        float: Percentage between 0 and 100
    """
    # Ensure score is in 0-1 range
    score = max(0, min(1.0, score))
    
    # First apply a pre-conditioning transformation to spread out the raw scores
    # This helps ensure we're using the full scoring range
    if score > 0.5:
        # Boost higher scores even more before mapping
        transformed_score = 0.5 + (score - 0.5) ** 0.7
    else:
        # Compress lower scores
        transformed_score = score * 0.5 / 0.5
        
    # Now apply our tier-based mapping with the transformed score
    if transformed_score > 0.8:  # Top tier
        percentage = 85 + (transformed_score - 0.8) * 150  # Map 0.8-1.0 to 85-100%
    elif transformed_score > 0.6:  # High tier
        percentage = 70 + (transformed_score - 0.6) * 75  # Map 0.6-0.8 to 70-85%
    elif transformed_score > 0.4:  # Medium tier
        percentage = 60 + (transformed_score - 0.4) * 50  # Map 0.4-0.6 to 60-70%
    else:  # Low tier
        percentage = transformed_score * 150  # Map 0-0.4 to 0-60%
    
    # Ensure we never exceed 100%
    return round(min(100.0, percentage), 1) 