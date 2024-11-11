# File: app.py

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Method, MethodTechnologyService, Task, Technology
from math import pi

# Database setup
engine = create_engine('sqlite:///fuel_cell_database.db')
Session = sessionmaker(bind=engine)
session = Session()

st.title("Fuel Cell Modeling Monte Carlo Simulation")

# Sidebar to view data from the database
st.sidebar.header("Database Viewer")

# View methods by task
if st.sidebar.checkbox("View Methods by Task"):
    tasks = session.query(Task).all()
    for task in tasks:
        st.sidebar.write(f"**Task {task.task_code}**")
        methods = session.query(Method).filter_by(task_id=task.task_id).all()
        for method in methods:
            st.sidebar.write(f"- {method.name} ({method.method_type})")

# View methods by technology
if st.sidebar.checkbox("View Methods by Technology"):
    technologies = session.query(Technology).all()
    for tech in technologies:
        st.sidebar.write(f"**Technology: {tech.name}**")
        methods = session.query(MethodTechnologyService).filter_by(technology_id=tech.technology_id).all()
        for method_service in methods:
            method = session.query(Method).filter_by(method_id=method_service.method_id).first()
            if method:
                st.sidebar.write(f"- {method.name}")

# Method selection and individual weight input
st.header("Select Methods to Bundle")
methods = session.query(Method).all()
selected_methods = []
method_weights = {}

# Display methods as checkboxes
for method in methods:
    if st.checkbox(f"{method.name} ({method.maturity})"):
        selected_methods.append(method)
        # Individual weight sliders for each selected method
        cost_w = st.slider(f"Cost Weight for {method.name}", 0.0, 2.0, 1.0, step=0.1)
        maturity_w = st.slider(f"Maturity Weight for {method.name}", 0.0, 2.0, 1.0, step=0.1)
        integration_w = st.slider(f"Integration Weight for {method.name}", 0.0, 2.0, 1.0, step=0.1)
        interoperability_w = st.slider(f"Interoperability Weight for {method.name}", 0.0, 2.0, 1.0, step=0.1)
        method_weights[method.method_id] = {
            "cost_w": cost_w,
            "maturity_w": maturity_w,
            "integration_w": integration_w,
            "interoperability_w": interoperability_w,
        }

# Function to generate random samples from a normal distribution, bounded by min and max
def sample_normal_dist(min_val, max_val, std_dev=0.5):
    mean_val = (min_val + max_val) / 2
    return np.clip(np.random.normal(mean_val, std_dev), min_val, max_val)

# Monte Carlo Simulation function with additive aggregation and linear weighting
def monte_carlo_simulation(selected_methods, method_weights, n_simulations=10000):
    irl_scores = []
    for _ in range(n_simulations):
        total_irl = 0
        for method in selected_methods:
            service = session.query(MethodTechnologyService).filter_by(method_id=method.method_id).first()
            if service:
                # Sample each parameter using a normal distribution within the min/max bounds
                cost_score = sample_normal_dist(service.cost_min, service.cost_max)
                maturity_score = sample_normal_dist(service.maturity_min, service.maturity_max)
                integration_score = sample_normal_dist(service.integration_min, service.integration_max)
                interoperability_score = sample_normal_dist(service.interoperability_min, service.interoperability_max)

                # Get weights for each parameter
                weights = method_weights[method.method_id]
                
                # Calculate a linearly weighted score for each method
                weighted_score = (
                    weights["cost_w"] * cost_score +
                    weights["maturity_w"] * maturity_score +
                    weights["integration_w"] * integration_score +
                    weights["interoperability_w"] * interoperability_score
                )
                
                # Sum scores across all methods in the bundle (additive aggregation)
                total_irl += weighted_score
        # Normalize by the total weights and number of methods to keep IRL in range
        normalization_factor = sum(weights.values()) * len(selected_methods)
        irl_scores.append(total_irl / normalization_factor)  # Average IRL score
    return np.array(irl_scores)

# Function to generate radar chart for the selected methods
def generate_radar_chart(selected_methods):
    # Define categories and initialize arrays for parameter averages
    categories = ['Maturity', 'Interoperability', 'Integration', 'Cost']
    avg_values = {category: [] for category in categories}

    # Collect scores for each parameter across selected methods
    for method in selected_methods:
        service = session.query(MethodTechnologyService).filter_by(method_id=method.method_id).first()
        if service:
            avg_values['Maturity'].append((service.maturity_min + service.maturity_max) / 2)
            avg_values['Interoperability'].append((service.interoperability_min + service.interoperability_max) / 2)
            avg_values['Integration'].append((service.integration_min + service.integration_max) / 2)
            avg_values['Cost'].append((service.cost_min + service.cost_max) / 2)
    
    # Compute average values for radar chart
    values = [np.mean(avg_values[cat]) for cat in categories]
    values += values[:1]  # Close the radar chart

    # Set up the radar chart
    num_vars = len(categories)
    angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
    angles += angles[:1]  # Close the radar chart

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    # Draw one axe per variable and add labels
    plt.xticks(angles[:-1], categories, color='grey', size=8)

    # Draw y-labels
    ax.set_rlabel_position(0)
    plt.yticks([2, 4, 6, 8], ["2", "4", "6", "8"], color="grey", size=7)
    plt.ylim(0, 9)

    # Plot data
    ax.plot(angles, values, linewidth=2, linestyle='solid')
    ax.fill(angles, values, 'b', alpha=0.1)

    # Title and display
    plt.title('Average Values for Selected Methods', size=14, color='blue', y=1.1)
    st.pyplot(fig)

# Run simulation and display radar chart on button click
if st.button("Run Simulation") and selected_methods:
    scores = monte_carlo_simulation(selected_methods, method_weights)
    
    # Display results
    st.write("Mean IRL Score:", np.mean(scores))
    st.write("Standard Deviation:", np.std(scores))
    percentiles = np.percentile(scores, [5, 50, 95])
    st.write(f"5th Percentile: {percentiles[0]}, Median: {percentiles[1]}, 95th Percentile: {percentiles[2]}")
    
    # Plot results
    fig, ax = plt.subplots()
    ax.hist(scores, bins=50, color="skyblue", edgecolor="black")
    st.pyplot(fig)

    # Generate and display radar chart
    st.header("Radar Chart of Average Values for Selected Methods")
    generate_radar_chart(selected_methods)
