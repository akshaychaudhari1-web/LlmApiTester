import subprocess
import sys
import tempfile
import os
import time
import logging

def execute_python_code(code):
    """
    Execute Python code safely and return output, errors, and execution time
    """
    start_time = time.time()
    
    try:
        # Create a temporary file to execute the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # Execute the code using subprocess
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                env=dict(os.environ, PYTHONPATH=os.getcwd())
            )
            
            execution_time = time.time() - start_time
            
            return {
                'output': result.stdout,
                'error': result.stderr,
                'return_code': result.returncode,
                'execution_time': round(execution_time, 3)
            }
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        return {
            'output': '',
            'error': 'Code execution timed out (30 seconds limit)',
            'return_code': -1,
            'execution_time': round(execution_time, 3)
        }
    except Exception as e:
        execution_time = time.time() - start_time
        logging.error(f"Code execution error: {str(e)}")
        return {
            'output': '',
            'error': f'Execution error: {str(e)}',
            'return_code': -1,
            'execution_time': round(execution_time, 3)
        }
