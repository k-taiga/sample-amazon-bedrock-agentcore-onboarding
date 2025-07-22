#!/usr/bin/env python3
"""
Test script for deploying cost_estimator_agent.py to AWS AgentCore Runtime

This script demonstrates the complete deployment workflow:
1. Prepare the agent for deployment (annotations and IAM role)
2. Deploy to AWS AgentCore Runtime
3. Test the deployed agent
4. Clean up resources

Usage:
    # Deploy the agent
    uv run test_register_agent.py deploy
    
    # Test the deployed agent
    uv run test_register_agent.py test --agent <agent_arn>
    
    # Clean up (delete runtime and IAM role)
    uv run test_register_agent.py cleanup
"""

import sys
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

# Add the current directory to Python path to import register_agent
sys.path.insert(0, str(Path(__file__).parent))

from register_agent import (
    AgentPreparer,
    AgentDeployer, 
    AgentInvoker,
    ResourceManager,
    DEFAULT_REGION
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

# Constants
AGENT_SOURCE_DIR = "../01_code_interpreter/cost_estimator_agent"
TEST_ARCHITECTURE = """
Web application architecture with:
- Application Load Balancer
- 2 EC2 instances (t3.medium) behind the load balancer
- RDS MySQL database (db.t3.micro)
- S3 bucket for static assets (100 GB storage)
- CloudFront distribution

Expected monthly usage:
- 100,000 requests per month
- 50 GB data transfer out
- RDS: 20 GB storage
"""


def prepare_agent(region: str = DEFAULT_REGION) -> str:
    """
    Prepare the cost estimator agent for deployment
    
    Args:
        region: AWS region
        
    Returns:
        Path to deployment directory
    """
    console.print(Panel.fit(
        "[bold blue]Step 1: Preparing Cost Estimator Agent for Deployment[/bold blue]",
        border_style="blue"
    ))
    
    console.print(f"📁 Source directory: [cyan]{AGENT_SOURCE_DIR}[/cyan]")
    console.print(f"🌍 AWS region: [cyan]{region}[/cyan]")
    
    preparer = AgentPreparer(AGENT_SOURCE_DIR, region)
    
    try:
        # Create deployment directory by copying source directory and create IAM role
        console.print("\n📦 Creating deployment directory and IAM role...")
        deployment_dir = preparer.prepare()
        console.print(f"✅ Deployment directory: [green]{deployment_dir}[/green]")
        return deployment_dir
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Agent preparation failed: {e}[/bold red]")
        raise


def deploy_agent(deployment_dir: str, region: str = DEFAULT_REGION) -> str:
    """
    Deploy the prepared agent to AWS AgentCore Runtime
    
    Args:
        deployment_dir: Path to deployment directory
        region: AWS region
        
    Returns:
        Agent ARN
    """
    console.print(Panel.fit(
        "[bold blue]Step 2: Deploying to AWS AgentCore Runtime[/bold blue]",
        border_style="blue"
    ))
    
    deployer = AgentDeployer(Path(deployment_dir), region)
    
    try:
        console.print(f"🚀 Deploying from: [cyan]{deployment_dir}[/cyan]")
        
        # Deploy to runtime
        agent_arn = deployer.deploy()
        
        # Display deployment success
        console.print("\n[bold green]✅ Deployment successful![/bold green]")            
        console.print(f"Agent ARN : {agent_arn}")
        return agent_arn
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Deployment failed: {e}[/bold red]")
        raise


def test_agent(agent_arn: str, region: str = DEFAULT_REGION) -> str:
    """
    Test the deployed agent with a sample architecture
    
    Args:
        agent_arn: ARN of the deployed agent
        region: AWS region
        
    Returns:
        Agent response
    """
    console.print(Panel.fit(
        "[bold blue]Step 3: Testing Deployed Agent[/bold blue]",
        border_style="blue"
    ))

    invoker = AgentInvoker(agent_arn, region)
    
    try:
        console.print("📋 Test architecture:")
        console.print(Panel(TEST_ARCHITECTURE, expand=False))
        
        console.print(f"\n🤖 Invoking agent with ARN: [cyan]{agent_arn}[/cyan]")
        console.print("⏳ This may take a few minutes as the agent analyzes pricing...")
        
        # Invoke the agent
        response = invoker.invoke(TEST_ARCHITECTURE)
        
        console.print("\n[bold green]✅ Agent response received![/bold green]")
        console.print(response)
        
        return response
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Agent test failed: {e}[/bold red]")
        raise


def cleanup_resources(region: str = DEFAULT_REGION, delete_role: bool = True) -> None:
    """
    Clean up AWS resources
    
    Args:
        region: AWS region
        delete_role: Whether to delete the IAM role
    """
    console.print(Panel.fit(
        "[bold blue]Step 4: Cleaning Up Resources[/bold blue]",
        border_style="blue"
    ))
    
    # Extract agent name from source directory
    agent_name = Path(AGENT_SOURCE_DIR).name
    manager = ResourceManager(agent_name, region)
    
    try:
        console.print(f"🗑️ Deleting runtime: [cyan]{agent_name}[/cyan]")
        if delete_role:
            console.print("🔐 Will also delete IAM role")
        
        manager.delete_runtime(delete_role)
        
        console.print("\n[bold green]✅ Cleanup completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Cleanup failed: {e}[/bold red]")
        raise


# CLI Commands
@click.group()
def cli():
    """Test deployment of AWS Cost Estimator Agent to AgentCore Runtime"""
    pass


@cli.command()
@click.option('--region', default=DEFAULT_REGION, help='AWS region')
def prepare(region: str):
    """Prepare the cost estimator agent for deployment"""
    console.print("[bold]🚀 AWS Cost Estimator Agent Preparation[/bold]\n")
    
    try:
        deployment_dir = prepare_agent(region)
        
        console.print("\n[bold green]🎉 Preparation completed successfully![/bold green]")
        console.print(f"Deployment directory: [cyan]{deployment_dir}[/cyan]")
        console.print("Next step: [cyan]uv run test_register_agent.py deploy[/cyan]")
        
    except Exception as e:
        console.print(f"\n[bold red]💥 Preparation failed: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.option('--region', default=DEFAULT_REGION, help='AWS region')
def deploy(region: str):
    """Deploy the cost estimator agent"""
    console.print("[bold]🚀 AWS Cost Estimator Agent Deployment[/bold]\n")
    
    try:
        # Step 1: Prepare
        deployment_dir = prepare_agent(region)
        
        # Step 2: Deploy  
        agent_arn = deploy_agent(deployment_dir, region)
        
        console.print("\n[bold green]🎉 Deployment completed successfully![/bold green]")
        console.print(f"Agent ARN: [cyan]{agent_arn}[/cyan]")
        console.print(f"Next step: [cyan]uv run test_register_agent.py test --agent {agent_arn}[/cyan]")
        
    except Exception as e:
        console.print(f"\n[bold red]💥 Deployment failed: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.option('--region', default=DEFAULT_REGION, help='AWS region')
@click.option('--agent', required=True, help='Agent ARN')
def test(region: str, agent: str):
    """Test the deployed agent"""
    console.print("[bold]🧪 Testing Deployed Cost Estimator Agent[/bold]\n")
    
    try:
        test_agent(agent, region)        
        console.print("\n[bold green]🎉 Agent test completed successfully![/bold green]")
        console.print("Cleanup: [cyan]uv run test_register_agent.py cleanup[/cyan]")
        
    except Exception as e:
        console.print(f"\n[bold red]💥 Agent test failed: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.option('--region', default=DEFAULT_REGION, help='AWS region')
@click.option('--keep-role', is_flag=True, help='Keep IAM role after cleanup')
def cleanup(region: str, keep_role: bool):
    """Clean up deployed resources"""
    console.print("[bold]🧹 Cleaning Up Resources[/bold]\n")
    
    if click.confirm('Are you sure you want to delete the deployed agent?'):
        try:
            cleanup_resources(region, delete_role=not keep_role)
            
            console.print("\n[bold green]🎉 Cleanup completed successfully![/bold green]")
            
        except Exception as e:
            console.print(f"\n[bold red]💥 Cleanup failed: {e}[/bold red]")
            sys.exit(1)
    else:
        console.print("[yellow]Cleanup cancelled[/yellow]")


@cli.command()
@click.option('--region', default=DEFAULT_REGION, help='AWS region')
def full_demo(region: str):
    """Run complete deployment demo (deploy -> test -> cleanup)"""
    console.print("[bold]🎬 Running Full Deployment Demo[/bold]\n")
    
    try:
        # Complete workflow
        console.print("1️⃣ Preparing agent...")
        deployment_dir = prepare_agent(region)
        
        console.print("\n2️⃣ Deploying to runtime...")
        agent_arn = deploy_agent(deployment_dir, region)
        
        console.print("\n3️⃣ Testing agent...")
        test_agent(agent_arn, region)
        
        # Ask if user wants to cleanup
        if click.confirm('\nDo you want to clean up the deployed resources?'):
            console.print("\n4️⃣ Cleaning up...")
            cleanup_resources(region)
            
        console.print("\n[bold green]🎉 Full demo completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"\n[bold red]💥 Demo failed: {e}[/bold red]")
        
        # Offer cleanup on failure
        if click.confirm('Do you want to attempt cleanup of any created resources?'):
            cleanup_resources(region)
        
        sys.exit(1)


if __name__ == '__main__':
    cli()