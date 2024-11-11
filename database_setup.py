# File: database_setup.py

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import random

Base = declarative_base()

# Define tables based on ERD schema
class Project(Base):
    __tablename__ = 'projects'
    project_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class Task(Base):
    __tablename__ = 'tasks'
    task_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    task_code = Column(String, unique=True, nullable=False)
    description = Column(String)
    partner = Column(String)
    contact_person = Column(String)
    email = Column(String)

class Method(Base):
    __tablename__ = 'methods'
    method_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.task_id'))
    method_type = Column(String)
    name = Column(String)
    objective = Column(String)
    maturity = Column(String)
    category = Column(String)
    unique_id = Column(String, unique=True)

class Technology(Base):
    __tablename__ = 'technologies'
    technology_id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)

class MethodTechnologyService(Base):
    __tablename__ = 'method_technology_services'
    service_id = Column(Integer, primary_key=True)
    method_id = Column(Integer, ForeignKey('methods.method_id'))
    technology_id = Column(Integer, ForeignKey('technologies.technology_id'))
    maturity_min = Column(Float)
    maturity_max = Column(Float)
    cost_min = Column(Float)
    cost_max = Column(Float)
    interoperability_min = Column(Float)
    interoperability_max = Column(Float)
    integration_min = Column(Float)
    integration_max = Column(Float)

# Create the SQLite database
engine = create_engine('sqlite:///fuel_cell_database.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Populate tables with synthetic data
def populate_data():
    # Create project if it doesn't exist
    project = session.query(Project).filter_by(name="DECODE").first()
    if not project:
        project = Project(name="DECODE")
        session.add(project)
        session.commit()
    
    # Create tasks
    tasks_data = [
        {"task_code": "T1.2", "description": "Fuel cell analysis task 1", "project_id": project.project_id},
        {"task_code": "T2.1", "description": "Fuel cell analysis task 2", "project_id": project.project_id},
        {"task_code": "T3.1", "description": "Fuel cell analysis task 3", "project_id": project.project_id},
    ]
    tasks = {}
    for task_data in tasks_data:
        task = session.query(Task).filter_by(task_code=task_data["task_code"]).first()
        if not task:
            task = Task(**task_data)
            session.add(task)
            session.commit()
        tasks[task_data["task_code"]] = task
    
    # Create PEMFC technology if it doesn't exist
    technology = session.query(Technology).filter_by(name="PEMFC").first()
    if not technology:
        technology = Technology(name="PEMFC", description="Polymer Electrolyte Membrane Fuel Cell")
        session.add(technology)
        session.commit()

    # Create methods for each task
    methods_data = [
        {"name": "X-ray Tomographic Microscopy", "task_code": "T1.2", "method_type": "Imaging", "maturity": "TRL 5"},
        {"name": "Neutron Imaging", "task_code": "T1.2", "method_type": "Imaging", "maturity": "TRL 6"},
        {"name": "Impedance Spectroscopy", "task_code": "T1.2", "method_type": "Spectroscopy", "maturity": "TRL 7"},
        {"name": "Atomic Force Microscopy", "task_code": "T2.1", "method_type": "Microscopy", "maturity": "TRL 6"},
        {"name": "Electron Tomography", "task_code": "T2.1", "method_type": "Tomography", "maturity": "TRL 7"},
        {"name": "Thermal Neutron Radiography", "task_code": "T2.1", "method_type": "Radiography", "maturity": "TRL 5"},
        {"name": "Density Functional Theory", "task_code": "T3.1", "method_type": "Simulation", "maturity": "TRL 8"},
        {"name": "Synchrotron Radiation", "task_code": "T3.1", "method_type": "Radiation", "maturity": "TRL 7"},
        {"name": "FIB/SEM Sectioning", "task_code": "T3.1", "method_type": "Sectioning", "maturity": "TRL 6"},
        {"name": "Raman Spectroscopy", "task_code": "T3.1", "method_type": "Spectroscopy", "maturity": "TRL 5"},
    ]
    for method_data in methods_data:
        task = tasks[method_data["task_code"]]
        method = session.query(Method).filter_by(name=method_data["name"]).first()
        if not method:
            new_method = Method(
                name=method_data["name"],
                task_id=task.task_id,
                method_type=method_data["method_type"],
                maturity=method_data["maturity"],
                unique_id=f"{method_data['task_code']}-{method_data['name'][:3].upper()}"
            )
            session.add(new_method)
            session.commit()
    
    # Populate MethodTechnologyService with synthetic scoring data
    for method in session.query(Method).all():
        service = MethodTechnologyService(
            method_id=method.method_id,
            technology_id=technology.technology_id,
            maturity_min=random.uniform(4, 6),
            maturity_max=random.uniform(7, 9),
            cost_min=random.uniform(3, 5),
            cost_max=random.uniform(6, 8),
            interoperability_min=random.uniform(4, 6),
            interoperability_max=random.uniform(7, 9),
            integration_min=random.uniform(4, 6),
            integration_max=random.uniform(7, 9)
        )
        session.add(service)
    session.commit()

populate_data()
