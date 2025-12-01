"""
Lambda Service for Agent Factory

Creates and manages Lambda functions that serve as tools for agents via AgentCore Gateway.
"""

import json
import logging
import os
import zipfile
import io
import textwrap
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class LambdaToolSpec:
    """Specification for a Lambda-based tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler_code: str


class LambdaServiceError(Exception):
    """Base exception for Lambda service errors"""
    pass


class LambdaService:
    """
    Service for creating and managing Lambda functions as agent tools.
    
    These Lambda functions are invoked by AgentCore Gateway and provide
    custom capabilities to agents.
    """
    
    def __init__(self, region_name: str = "us-west-2"):
        """
        Initialize Lambda Service.
        
        Args:
            region_name: AWS region
        """
        self.region_name = region_name
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        logger.info(f"LambdaService initialized for region {region_name}")
    
    def create_tool_function(
        self,
        tool_spec: LambdaToolSpec,
        execution_role_arn: str,
        function_prefix: str = "agent-tool"
    ) -> Dict[str, Any]:
        """
        Create a Lambda function for a tool.
        
        Args:
            tool_spec: Tool specification
            execution_role_arn: IAM role ARN for Lambda execution
            function_prefix: Prefix for function name
        
        Returns:
            Dict with function_arn, function_name, and tool details
        
        Raises:
            LambdaServiceError: If function creation fails
        """
        try:
            # Generate function name
            safe_name = tool_spec.name.lower().replace(' ', '-').replace('_', '-')
            function_name = f"{function_prefix}-{safe_name}"
            
            logger.info(f"Creating Lambda function: {function_name}")
            
            # Generate Lambda code
            lambda_code = self._generate_lambda_code(tool_spec)
            
            # Create deployment package
            zip_file = self._create_lambda_package(lambda_code)
            
            try:
                # Try to get existing function
                self.lambda_client.get_function(FunctionName=function_name)
                
                # Update existing function
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_file
                )
                
                logger.info(f"Updated existing Lambda function: {function_name}")
                
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create new function
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.11',
                    Role=execution_role_arn,
                    Handler='lambda_function.handler',
                    Code={'ZipFile': zip_file},
                    Description=tool_spec.description,
                    Timeout=30,
                    MemorySize=512,
                    Environment={
                        'Variables': {
                            'TOOL_NAME': tool_spec.name,
                            'TOOL_DESCRIPTION': tool_spec.description
                            # Note: AWS_REGION is automatically provided by Lambda runtime
                        }
                    }
                )
                
                logger.info(f"Created new Lambda function: {function_name}")
            
            function_arn = response['FunctionArn']
            
            return {
                'function_arn': function_arn,
                'function_name': function_name,
                'tool_name': tool_spec.name,
                'tool_description': tool_spec.description,
                'input_schema': tool_spec.input_schema
            }
            
        except ClientError as e:
            error_msg = f"Failed to create Lambda function: {e}"
            logger.error(error_msg)
            raise LambdaServiceError(error_msg) from e
    
    def _generate_lambda_code(self, tool_spec: LambdaToolSpec) -> str:
        """
        Generate Lambda function code for a tool.
        Uses inline generation for reliability (no template files needed).
        
        Args:
            tool_spec: Tool specification
        
        Returns:
            Python code as string
        """
        # Process handler code
        handler_code = tool_spec.handler_code.strip()
        
        logger.info(f"Generating Lambda for tool: {tool_spec.name}")
        
        # Check if the LLM provided a complete Lambda function
        if 'def handler' in handler_code or 'def lambda_handler' in handler_code:
            logger.info("LLM provided complete Lambda function, using as-is")
            # Ensure it has proper imports
            if 'import json' not in handler_code:
                handler_code = 'import json\nimport logging\n\nlogger = logging.getLogger()\nlogger.setLevel(logging.INFO)\n\n' + handler_code
            return handler_code
        
        # LLM provided just the tool logic - wrap it
        logger.info("LLM provided tool logic only, wrapping in handler")
        
        # Ensure handler code is not empty
        if not handler_code.strip():
            handler_code = "pass  # No implementation provided"
        
        # Check if handler code needs specific imports (before removing them)
        needs_boto3 = 'boto3' in handler_code or 'dynamodb' in handler_code.lower()
        needs_datetime = 'datetime' in handler_code
        needs_os = 'os.environ' in handler_code or 'os.getenv' in handler_code
        # Always add Decimal if using DynamoDB (for numeric values)
        needs_decimal = 'Decimal' in handler_code or 'dynamodb' in handler_code.lower() or 'put_item' in handler_code
        
        # Remove ALL import statements from handler code to avoid shadowing top-level imports
        # This handles: import x, from x import y, from x import y, z
        import re
        # Remove import lines (handles multi-word module names and multiple imports)
        handler_code = re.sub(r'^\s*import\s+[\w\.]+\s*$', '', handler_code, flags=re.MULTILINE)
        handler_code = re.sub(r'^\s*from\s+[\w\.]+\s+import\s+.+$', '', handler_code, flags=re.MULTILINE)
        # Clean up any resulting blank lines
        handler_code = '\n'.join(line for line in handler_code.split('\n') if line.strip() or not line)
        handler_code = handler_code.lstrip('\n')
        
        # Auto-fix DynamoDB numeric values: wrap parameters.get() calls for numeric fields in Decimal
        # This prevents the "Float types are not supported" error
        if 'put_item' in handler_code and needs_decimal:
            # Common numeric field names that should be Decimal
            numeric_fields = ['amount', 'price', 'cost', 'total', 'quantity', 'days', 'hours', 'count', 'value', 'balance']
            for field in numeric_fields:
                # Match: 'field': parameters.get('field') or 'field': parameters.get('field', default)
                # Replace with: 'field': Decimal(str(parameters.get('field'))) or Decimal(str(parameters.get('field', default)))
                # Pattern matches the field assignment in put_item
                pattern = rf"(['\"]){field}\1\s*:\s*parameters\.get\((['\"]){field}\2(,\s*[^)]+)?\)"
                
                def replace_with_decimal(match):
                    quote = match.group(1)
                    field_quote = match.group(2)
                    default_part = match.group(3) if match.group(3) else ''
                    return f"{quote}{field}{quote}: Decimal(str(parameters.get({field_quote}{field}{field_quote}{default_part})))"
                
                handler_code = re.sub(pattern, replace_with_decimal, handler_code)
        
        # Indent the handler code properly (8 spaces for inside try block)
        handler_code_indented = textwrap.indent(handler_code, '        ')
        
        # Build imports - add all needed imports at the top level
        imports = ['import json', 'import logging']
        if needs_boto3:
            imports.append('import boto3')
        if needs_datetime:
            imports.append('from datetime import datetime')
        if needs_os:
            imports.append('import os')
        if needs_decimal:
            imports.append('from decimal import Decimal')
        
        imports_str = '\n'.join(imports)
        
        # Use f-string with properly indented code
        code = f'''{imports_str}

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """Lambda handler for {tool_spec.name} tool"""
    try:
        logger.info(f"Tool {tool_spec.name} invoked with event: {{json.dumps(event)}}")
        
        # Extract parameters
        parameters = event.get('parameters', event)
        
        # Execute tool logic
{handler_code_indented}
        
    except Exception as e:
        logger.error(f"Tool execution failed: {{str(e)}}", exc_info=True)
        return {{
            'statusCode': 500,
            'body': json.dumps({{'error': str(e)}})
        }}
'''
        return code
    
    def _create_lambda_package(self, code: str) -> bytes:
        """
        Create a Lambda deployment package (ZIP file).
        
        Args:
            code: Python code
        
        Returns:
            ZIP file as bytes
        """
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('lambda_function.py', code)
        
        return zip_buffer.getvalue()
    
    def delete_function(self, function_name: str) -> bool:
        """
        Delete a Lambda function.
        
        Args:
            function_name: Name of the function to delete
        
        Returns:
            True if successful
        """
        try:
            self.lambda_client.delete_function(FunctionName=function_name)
            logger.info(f"Deleted Lambda function: {function_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete function: {e}")
            return False
