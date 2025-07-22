#!/usr/bin/env python3
"""
AgentCore Runtime - Agent Registration and Management Tool

A simple tool for deploying AI agents to Amazon Bedrock AgentCore Runtime.
"""

import os
import json
import shutil
import logging
import time
from pathlib import Path
import boto3
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from botocore.exceptions import ClientError
from bedrock_agentcore_starter_toolkit import Runtime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()

# Constants
DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
DEPLOYMENTS_DIR = Path('./deployment')


class AgentPreparer:
    """Handles preparation of agent for deployment"""
    
    def __init__(self, source_dir: str, region: str = DEFAULT_REGION):
        self.source_dir = Path(source_dir)
        self.region = region
        self.iam_client = boto3.client('iam', region_name=region)
    
    @property
    def agent_name(self) -> str:
        """
        Extract agent name from the source directory (last folder name)
        
        Returns:
            str: Name of the agent
        """
        return self.source_dir.name if self.source_dir.is_dir() else self.source_dir.stem

    def prepare(self) -> Path:
        """
        Prepare agent for deployment by creating deployment directory and IAM role
            
        Returns:
            Path: Path to the deployment directory
        """
        # Create deployment directory
        deployment_dir = self.create_source_directory()
        
        # Create IAM role
        role_info = self.create_agentcore_role()
        
        # Save role info to deployment directory for later use
        role_info_path = DEPLOYMENTS_DIR / 'iam_role.json'
        with open(role_info_path, 'w') as f:
            json.dump(role_info, f, indent=2)
        
        return deployment_dir

    def create_source_directory(self) -> str:
        """
        Create deployment directory by copying entire source directory
            
        Returns:
            Path to the deployment directory
        """
        logger.info(f"Creating deployment directory from {self.source_dir}")

        # Validate source directory exists
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")

        # Create deployment directory
        target_dir = DEPLOYMENTS_DIR / self.agent_name
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy Python files from source directory
        logger.info(f"Copying Python files from {self.source_dir} to {target_dir}")
        for file_path in self.source_dir.glob("*.py"):
            dest_path = target_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            logger.info(f"Copied {file_path.name}")
            
        logger.info(f"Source directory is copied to deployment directory: {DEPLOYMENTS_DIR}")
        return str(DEPLOYMENTS_DIR)

    def create_agentcore_role(self) -> dict:
        """
        Create IAM role with AgentCore permissions
        Based on https://github.com/awslabs/amazon-bedrock-agentcore-samples
                    
        Returns:
            Role information including ARN
        """
        role_name = f"AgentCoreRole-{self.agent_name}"
        logger.info(f"Creating IAM role: {role_name}")
        
        # Get account ID
        sts_client = boto3.client('sts', region_name=self.region)
        account_id = sts_client.get_caller_identity()['Account']
        
        # Create trust policy
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock-agentcore.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceAccount": account_id
                        },
                        "ArnLike": {
                            "aws:SourceArn": f"arn:aws:bedrock-agentcore:{self.region}:{account_id}:*"
                        }
                    }
                }
            ]
        }
        
        # Create execution policy
        execution_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockPermissions",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "ECRImageAccess",
                    "Effect": "Allow",
                    "Action": [
                        "ecr:BatchGetImage",
                        "ecr:GetDownloadUrlForLayer"
                    ],
                    "Resource": [
                        f"arn:aws:ecr:{self.region}:{account_id}:repository/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:DescribeLogStreams",
                        "logs:CreateLogGroup"
                    ],
                    "Resource": [
                        f"arn:aws:logs:{self.region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:DescribeLogGroups"
                    ],
                    "Resource": [
                        f"arn:aws:logs:{self.region}:{account_id}:log-group:*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        f"arn:aws:logs:{self.region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                    ]
                },
                {
                    "Sid": "ECRTokenAccess",
                    "Effect": "Allow",
                    "Action": [
                        "ecr:GetAuthorizationToken"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "xray:PutTraceSegments",
                        "xray:PutTelemetryRecords",
                        "xray:GetSamplingRules",
                        "xray:GetSamplingTargets"
                        ],
                    "Resource": [ "*" ]
                },
                {
                    "Effect": "Allow",
                    "Resource": "*",
                    "Action": "cloudwatch:PutMetricData",
                    "Condition": {
                        "StringEquals": {
                            "cloudwatch:namespace": "bedrock-agentcore"
                        }
                    }
                },
                {
                    "Sid": "GetAgentAccessToken",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:GetWorkloadAccessToken",
                        "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                        "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
                    ],
                    "Resource": [
                        f"arn:aws:bedrock-agentcore:{self.region}:{account_id}:workload-identity-directory/default*",
                        f"arn:aws:bedrock-agentcore:{self.region}:{account_id}:workload-identity-directory/default/workload-identity/{self.agent_name}-*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:CreateCodeInterpreter",
                        "bedrock-agentcore:StartCodeInterpreterSession",
                        "bedrock-agentcore:InvokeCodeInterpreter",
                        "bedrock-agentcore:StopCodeInterpreterSession",
                        "bedrock-agentcore:DeleteCodeInterpreter",
                        "bedrock-agentcore:ListCodeInterpreters",
                        "bedrock-agentcore:GetCodeInterpreter",
                        "bedrock-agentcore:GetCodeInterpreterSession",
                        "bedrock-agentcore:ListCodeInterpreterSessions"
                    ],
                    "Resource": "arn:aws:bedrock-agentcore:*:*:*"
                }
            ]
        }
        
        role_exists = False
        response = None

        try:
            response = self.iam_client.get_role(RoleName=role_name)
            logger.info(f"Role {role_name} already exists")
            role_exists = True
        except ClientError:
            pass

        if not role_exists:
            try:
                # Create role
                response = self.iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description=f'AgentCore execution role for {self.agent_name}'
                )
                logger.info(f"IAM role created successfully: {role_name}")
                
            except ClientError as e:
                logger.error(f"Failed to create IAM role: {e}")
                raise

            # Always ensure the execution policy is attached (for both new and existing roles)
            try:
                self.iam_client.put_role_policy(
                    RoleName=role_name,
                    PolicyName=f'{role_name}-ExecutionPolicy',
                    PolicyDocument=json.dumps(execution_policy)
                )
                
                time.sleep(10)
                    
                logger.info(f"Execution policy attached to role: {role_name}")
                
            except ClientError as e:
                logger.error(f"Failed to attach execution policy: {e}")
                raise

        return {
            'agent_name': self.agent_name,
            'role_name': role_name,
            'role_arn': response['Role']['Arn']
        }


class AgentDeployer:
    """Handles deployment to AgentCore Runtime using starter toolkit"""
    
    def __init__(self, deployment_dir: Path, region: str = DEFAULT_REGION):
        self.deployment_dir = deployment_dir
        self.region = region

    def deploy(self) -> str:
        """
        Deploy agent to AgentCore Runtime
            
        Returns:
            str: ARN of the deployed agent
        """
        
        # Load role information
        role_info_path = self.deployment_dir / 'iam_role.json'
        with open(role_info_path, 'r') as f:
            role_info = json.load(f)

        # Create and configure runtime
        agent_name = role_info['agent_name']
        logger.info(f"Deploying agent '{agent_name}' from {self.deployment_dir}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Creating and deploying runtime...", total=None)
            
            runtime = Runtime()
            
            # Configure the runtime with the deployment directory as entrypoint
            runtime.configure(
                entrypoint=f"{self.deployment_dir}/invoke.py",
                execution_role=role_info['role_arn'],
                agent_name=agent_name,
                requirements_file=f"{self.deployment_dir}/requirements.txt",
                region=self.region,
                protocol="HTTP"
            )
            
            # Launch the runtime
            launch_result = runtime.launch()
            
            # Wait for the runtime to reach a terminal state
            progress.update(task, description="Waiting for runtime to be ready...")
            status_response = runtime.status()
            status = status_response.endpoint['status']
            end_status = ['READY', 'CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']
            
            while status not in end_status:
                time.sleep(10)
                status_response = runtime.status()
                status = status_response.endpoint['status']
                progress.update(task, description=f"Current status: {status}...")
                
            if status != 'READY':
                logger.error(f"Runtime deployment failed with status: {status}")
                raise RuntimeError(f"Agent deployment failed with status: {status}")
                
            progress.update(task, completed=True, description="Deployment complete!")
        
        # Save deployment metadata
        logger.info(f"Deployment successful: {agent_name} : arn {launch_result.agent_arn}")
        return launch_result.agent_arn

class AgentInvoker:
    """Handles interaction with deployed agents"""
    
    def __init__(self, agent_arn: str, region: str = DEFAULT_REGION):
        self.region = region
        self.agent_arn = agent_arn
        self.agent_client = boto3.client('bedrock-agentcore', region_name=self.region)

    def invoke(self, message: str) -> str:
        """
        Invoke deployed agent
        
        Args:
            message: Message to send
            
        Returns:
            Agent response
        """
        logger.info(f"Invoking agent '{self.agent_arn}' with message: {message}")
            
        # Prepare the payload
        payload = json.dumps({"prompt": message}).encode()

        # Invoke the agent
        try:
            response = self.agent_client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_arn,
                qualifier="DEFAULT",
                payload=payload
            )

            if "text/event-stream" in response.get("contentType", ""):
                content = []
                for line in response["response"].iter_lines(chunk_size=1):
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            line = line[6:]
                            logger.info(line)
                            content.append(line)
                response_text = "\n".join(content)
            else:
                try:
                    events = []
                    for event in response.get("response", []):
                        events.append(event)
                except Exception as e:
                    events = [f"Error reading EventStream: {e}"]
                response_text = json.loads(events[0].decode("utf-8"))

            logger.info("Agent invocation successful")
            return response_text

        except Exception as e:
            logger.error(f"Failed to invoke agent: {e}")
            return f"Error: {str(e)}"


class ResourceManager:
    """Handles resource lifecycle management"""
    
    def __init__(self, agent_name: str, region: str = DEFAULT_REGION):
        self.region = region
        self.agent_name = agent_name
        self.iam_client = boto3.client('iam', region_name=region)

    def delete_runtime(self, delete_role: bool = False) -> None:
        """
        Delete agent runtime
        
        Args:
            delete_role: Whether to delete IAM role
        """
        logger.info(f"Deleting runtime: {self.agent_name}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Deleting runtime...", total=None)
            
            try:
                # Note: Runtime class may not have a delete method, this might need to be handled differently
                logger.warning("Runtime deletion may require manual cleanup via AWS console")
            except Exception as e:
                logger.warning(f"Failed to delete runtime: {e}")
                
            progress.update(task, completed=True)
            
            if delete_role:
                task = progress.add_task("Deleting IAM role...", total=None)
                self._delete_iam_role(self.agent_name)
                progress.update(task, completed=True)
                
        logger.info("Cleanup completed")
        
    def _delete_iam_role(self, agent_name: str) -> None:
        """Delete IAM role associated with agent"""
        role_name = f"AgentCoreRole-{agent_name}"
        
        try:
            # Delete inline policies first
            policies = self.iam_client.list_role_policies(RoleName=role_name)
            for policy_name in policies.get('PolicyNames', []):
                self.iam_client.delete_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name
                )
            
            # Delete role
            self.iam_client.delete_role(RoleName=role_name)
            logger.info(f"IAM role {role_name} deleted")
        except ClientError as e:
            logger.warning(f"Failed to delete IAM role: {e}")


# CLI Interface
@click.group()
def cli():
    """AgentCore Runtime deployment tool"""
    pass

@cli.command()
@click.option('--source-dir', required=True, help='Source directory to copy')
@click.option('--region', default=DEFAULT_REGION, help='AWS region')
def prepare(source_dir: str, region: str):
    """Prepare agent for deployment by copying source directory"""
    console.print(f"[bold blue]Preparing agent from: {source_dir}[/bold blue]")
    
    preparer = AgentPreparer(source_dir, region)
    
    try:
        console.print("\nPreparation start...!")
        deployment_dir = preparer.prepare()
        console.print("\n[bold green]Preparation complete![/bold green]")
        console.print(f"Next step: [cyan]uv run register_agent.py deploy {deployment_dir}[/cyan]")
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument('deployment_dir')
@click.option('--region', default=DEFAULT_REGION, help='AWS region')
def deploy(deployment_dir: str, region: str):
    """Deploy agent to runtime"""
    console.print(f"[bold blue]Deploying from: {deployment_dir}[/bold blue]")
    deployer = AgentDeployer(Path(deployment_dir), region)
    
    try:
        agent_arn = deployer.deploy()
        
        console.print("\n[bold green]Deployment successful![/bold green]")
        console.print(f"Agent ARN: [cyan]{agent_arn}[/cyan]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument('agent_arn')
@click.argument('message')
@click.option('--region', default=DEFAULT_REGION, help='AWS region')
def invoke(agent_arn: str, message: str, region: str):
    """Invoke deployed agent"""
    console.print(f"[bold blue]Invoking agent: {agent_arn}[/bold blue]")
    
    invoker = AgentInvoker(agent_arn, region)
    
    try:
        response = invoker.invoke(message)
        
        console.print("\n[bold green]Agent Response:[/bold green]")
        console.print(response)
        
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument('agent_name')
@click.option('--delete-role', is_flag=True, help='Also delete IAM role')
@click.option('--region', default=DEFAULT_REGION, help='AWS region')
def delete(agent_name: str, delete_role: bool, region: str):
    """Delete runtime"""
    console.print(f"[bold blue]Deleting runtime: {agent_name}[/bold blue]")
    
    if click.confirm('Are you sure you want to delete this runtime?'):
        manager = ResourceManager(agent_name, region)
        
        try:
            manager.delete_runtime(delete_role)
            console.print("\n[bold green]Runtime deleted successfully![/bold green]")
            
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            raise click.Abort()
    else:
        console.print("[yellow]Deletion cancelled[/yellow]")


if __name__ == '__main__':
    cli()
