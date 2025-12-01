"""
Employee Data Module
====================
This module generates synthetic employee data for the A2A demo.
In a real application, this would connect to a database or HR system.

Data Structure:
- SKILLS: Set of all possible employee skills
- EMPLOYEES: List of employee records with names and skills
"""

import random


# ============================================================================
# Sample Data: Names
# ============================================================================
# Common first and last names for generating realistic employee data
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", 
    "Jennifer", "Michael", "Linda", "William", "Elizabeth"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", 
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"
]


# ============================================================================
# Sample Data: Skills
# ============================================================================
# Comprehensive set of technical skills across different domains
SKILLS = {
    # Programming Languages
    "Kotlin", "Java", "Python", "JavaScript", "TypeScript",
    
    # Frontend Frameworks
    "React", "Angular",
    
    # Backend Frameworks
    "Spring Boot", "Node.js",
    
    # Cloud & DevOps
    "AWS", "Docker", "Kubernetes", "DevOps", "CI/CD",
    
    # Databases
    "SQL", "MongoDB",
    
    # Tools & Practices
    "Git", "REST API", "GraphQL",
    
    # Specialized Skills
    "Machine Learning"
}


# ============================================================================
# Generate Employee Dataset
# ============================================================================
# Create 100 unique employees with random skill combinations
# Each employee has:
#   - name: Full name (First Last)
#   - skills: List of 2-5 random skills from the SKILLS set
#
# Note: We use a dictionary comprehension to ensure unique names,
# then convert to a list for easier iteration
EMPLOYEES = list({
    emp["name"]: emp for emp in [
        {
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "skills": random.sample(list(SKILLS), random.randint(2, 5))
        }
        for i in range(100)
    ]
}.values())


# ============================================================================
# Data Statistics (for reference)
# ============================================================================
# Total unique skills: 20
# Total employees: ~100 (may be slightly less due to duplicate name removal)
# Skills per employee: 2-5 (randomly assigned)
#
# In Production:
# - Replace this with database queries
# - Add more employee attributes (department, role, experience, etc.)
# - Implement proper data validation
# - Add caching for performance
# - Consider privacy and data protection requirements