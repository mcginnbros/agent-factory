#!/usr/bin/env python3
"""
Tutorial 6: Multi-Agent A2A System Runner
==========================================
This script orchestrates a complete Agent-to-Agent (A2A) communication system.
It starts three services that work together:
  1. MCP Server (Port 8002) - Provides employee data
  2. Employee Agent (Port 8001) - Queries employee information
  3. HR Agent (Port 8000) - User-facing API that delegates to Employee Agent

This demonstrates how multiple agents can collaborate to solve complex tasks!
"""

# ============================================================================
# STEP 1: Import Required Libraries
# ============================================================================
import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path


# ============================================================================
# STEP 2: Setup Directory Paths
# ============================================================================
# Add the strands-a2a-inter-agent directory to Python path
# This allows us to run the agent scripts from this orchestrator
SCRIPT_DIR = Path(__file__).parent
A2A_DIR = SCRIPT_DIR / "strands-a2a-inter-agent"

# ============================================================================
# STEP 3: Define Helper Functions
# ============================================================================

def cleanup_ports():
    """
    Clean up any processes using the required ports.
    
    This ensures a clean start by killing any lingering processes
    from previous runs that might be occupying our ports.
    
    Ports used:
      - 8000: HR Agent (user-facing API)
      - 8001: Employee Agent (internal service)
      - 8002: MCP Server (data provider)
    """
    ports = [8000, 8001, 8002]
    
    for port in ports:
        try:
            # Find processes using this port
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                
                # Kill each process
                for pid in pids:
                    try:
                        subprocess.run(['kill', '-9', pid], check=False)
                        print(f"🧹 Killed process {pid} using port {port}")
                    except:
                        pass
        except:
            pass


def stream_output(process, name):
    """
    Stream process output in real-time for debugging.
    
    This function runs in a separate thread for each service,
    capturing and displaying their output with a service label.
    
    Args:
        process: The subprocess to monitor
        name: Display name for the service (e.g., "MCP", "EMPLOYEE", "HR")
    """
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f"[{name}] {line.rstrip()}")

# ============================================================================
# STEP 4: Main Orchestration Function
# ============================================================================

def main():
    """
    Main function that orchestrates the A2A system startup.
    
    This function:
    1. Validates environment configuration
    2. Cleans up any existing processes on required ports
    3. Starts all three services in sequence
    4. Monitors their health
    5. Handles graceful shutdown
    """
    print("🚀 Multi-Agent A2A System Runner")
    print("=" * 40)
    
    # Validate API key configuration
    api_key = os.getenv("api_key")
    if not api_key:
        print("⚠️  Warning: 'api_key' environment variable is not set!")
        print("Setting dummy key for infrastructure testing...")
        os.environ["api_key"] = "dummy-key-for-testing"
    
    # Clean up any existing processes on our ports
    print("🧹 Cleaning up ports...")
    cleanup_ports()
    time.sleep(1)
    
    # List to track all running processes
    processes = []
    
    try:
        # ====================================================================
        # SERVICE 1: Start MCP Server (Port 8002)
        # ====================================================================
        # The MCP Server provides employee data through MCP protocol
        # It's the foundation of our data layer
        print("\n🚀 Starting MCP Server (Port 8002)...")
        mcp_process = subprocess.Popen(
            [sys.executable, "server.py"],
            cwd=str(A2A_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(mcp_process)
        
        # Start output streaming thread for real-time monitoring
        mcp_thread = threading.Thread(target=stream_output, args=(mcp_process, "MCP"))
        mcp_thread.daemon = True
        mcp_thread.start()
        
        print("⏳ Waiting for MCP Server to start...")
        time.sleep(5)
        
        # ====================================================================
        # SERVICE 2: Start Employee Agent (Port 8001)
        # ====================================================================
        # The Employee Agent connects to the MCP Server and provides
        # a higher-level interface for querying employee information
        print("\n🤖 Starting Employee Agent (Port 8001)...")
        employee_process = subprocess.Popen(
            [sys.executable, "employee-agent.py"],
            cwd=str(A2A_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(employee_process)
        
        # Start output streaming thread
        employee_thread = threading.Thread(target=stream_output, args=(employee_process, "EMPLOYEE"))
        employee_thread.daemon = True
        employee_thread.start()
        
        print("⏳ Waiting for Employee Agent to start...")
        time.sleep(5)
        
        # ====================================================================
        # SERVICE 3: Start HR Agent (Port 8000)
        # ====================================================================
        # The HR Agent is the user-facing API that delegates complex
        # queries to the Employee Agent using A2A communication
        print("\n👥 Starting HR Agent (Port 8000)...")
        hr_process = subprocess.Popen(
            [sys.executable, "hr-agent.py"],
            cwd=str(A2A_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(hr_process)
        
        # Start output streaming thread
        hr_thread = threading.Thread(target=stream_output, args=(hr_process, "HR"))
        hr_thread.daemon = True
        hr_thread.start()
        
        print("⏳ Waiting for HR Agent to start...")
        time.sleep(5)
        
        # ====================================================================
        # System Ready!
        # ====================================================================
        print("\n🎉 All services started successfully!")
        print("=" * 40)
        print("System Architecture:")
        print("  User → HR Agent (8000) → Employee Agent (8001) → MCP Server (8002)")
        print("\nTest the system:")
        print('  curl -X POST http://localhost:8000/inquire \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"question": "list employees with Python skills"}\'')
        print("\nPress Ctrl+C to stop all services")
        print("=" * 40)
        
        # ====================================================================
        # Monitor Process Health
        # ====================================================================
        # Keep running and monitor that all processes stay alive
        while True:
            # Check if any process has died unexpectedly
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    service_names = ["MCP Server", "Employee Agent", "HR Agent"]
                    print(f"\n❌ {service_names[i]} has stopped unexpectedly!")
                    return
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal, shutting down...")
    
    finally:
        # ====================================================================
        # Graceful Shutdown
        # ====================================================================
        print("🧹 Cleaning up processes...")
        
        for process in processes:
            if process.poll() is None:  # Process is still running
                try:
                    # Try graceful termination first
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful termination fails
                    process.kill()
                    process.wait()
        
        print("✅ All services stopped cleanly")


# ============================================================================
# Entry Point
# ============================================================================
if __name__ == "__main__":
    main()


# ============================================================================
# How A2A Communication Works:
# ============================================================================
# 1. User sends request to HR Agent (Port 8000)
# 2. HR Agent determines it needs employee data
# 3. HR Agent calls Employee Agent (Port 8001) via A2A protocol
# 4. Employee Agent queries MCP Server (Port 8002) for data
# 5. Data flows back: MCP → Employee Agent → HR Agent → User
#
# Benefits of A2A Architecture:
# - Separation of concerns (each agent has a specific role)
# - Scalability (agents can be scaled independently)
# - Reusability (Employee Agent can serve multiple clients)
# - Maintainability (easier to update individual agents)
# - Specialization (each agent can use different models/tools)
#
# Real-World Use Cases:
# - Customer service (routing agent → specialist agents)
# - Data processing pipelines (orchestrator → worker agents)
# - Complex workflows (coordinator → task-specific agents)
# - Microservices architecture with AI agents
