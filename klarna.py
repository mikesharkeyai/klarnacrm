import os
import json
import logging
import time
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set the API key
os.environ["OPENAI_API_KEY"] = "<YOUR-API-KEY>"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI()

def get_command_from_openai(prompt, context):
    logger.info("Sending request to OpenAI API")
    try:
        instructions = (
            "You are an AI assistant tasked with developing and improving a Customer Relationship Management (CRM) application for Klarna. "
            "You should iteratively improve the CRM, focusing on HTML, CSS and JavaScript files only. "
            "This is a working prototype, so you need to ensure that the application remains functional after each update. "
            "Do not use libraries or frameworks like React, Angular, or Vue. Just native javascript, css, and html."
            "Each update should replace the entire content of the file. "
            "Use the following command to interact with the file system:\n"
            "- `update_file`: Replace the entire content of a file.\n\n"
            "Context:\n{context}\n\nPrompt:\n{prompt}"
        )

        response = client.chat.completions.create(
            model="o1-mini",
            messages=[
                {
                    "role": "user",
                    "content": instructions.format(context=context, prompt=prompt)
                }
            ],
            max_completion_tokens=32000,
        )
        command = response.choices[0].message.content.strip()
        logger.info("Received response from OpenAI API")
        logger.debug(f"Full response: {command}")
        
        json_commands = extract_json(command)
        if json_commands:
            for cmd in json_commands:
                logger.info(f"Extracted JSON command for file: {cmd.get('filename', 'unknown')}")
                logger.debug(f"Command details: {json.dumps(cmd, indent=2)}")
            return json_commands
        else:
            logger.error("No valid JSON command found in the response")
            return None

    except Exception as e:
        logger.error(f"Error fetching command from OpenAI: {e}")
        return None

def extract_json(command):
    logger.info("Trying to extract JSON from OpenAI response")
    try:
        command = command.replace('```json', '').replace('```', '').strip()
        
        start = min(command.find('{'), command.find('['))
        end = max(command.rfind('}'), command.rfind(']'))
        
        if start != -1 and end != -1 and start < end:
            json_str = command[start:end+1]
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                logger.info(f"Successfully extracted {len(parsed)} JSON commands")
                return parsed
            else:
                logger.info("Successfully extracted 1 JSON command")
                return [parsed]
        else:
            logger.error("No JSON object found in the command")
            return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return None

def validate_command(cmd):
    if not isinstance(cmd, dict):
        logger.error("Command fail")
        return False
    if "action" not in cmd or "filename" not in cmd or "content" not in cmd:
        logger.error("Missing fields")
        return False
    if cmd["action"] != "update_file":
        logger.error(f"Invalid action: {cmd.get('action')}")
        return False
    if not cmd["filename"].endswith(('.html', '.js', '.css')):
        logger.error(f"Invalid filename: {cmd.get('filename')}")
        return False
    logger.info("Great success! Command is valid")
    return True

def unescape_content(content):
    logger.debug("Unescaping content")
    return content.encode().decode('unicode_escape')

def execute_command(command):
    if not command:
        logger.warning("No command to execute")
        return

    if not validate_command(command):
        logger.error("Invalid command structure")
        return

    filename = command["filename"]
    content = unescape_content(command["content"])

    logger.info(f"Updating file: {filename}")
    try:
        with open(filename, 'w') as f:
            f.write(content)
        logger.info(f"File '{filename}' successfully updated")
    except Exception as e:
        logger.error(f"Error: {e}")

def get_file_content(filepath):
    logger.info(f"Reading content of: {filepath}")
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        logger.info(f"Successfully read content from {filepath}")
        return content
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return ""
    except Exception as e:
        logger.error(f"Error reading file '{filepath}': {e}")
        return ""

def setup_selenium():
    logger.info("Selenium time...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    logger.info("Setup complete")
    return driver

def run_selenium_tests(driver):
    logger.info("Running test: Selenium edition")
    try:
        file_path = "file://" + os.path.abspath("index.html")
        logger.info(f"Loading page: {file_path}")
        driver.get(file_path)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(("tag name", "body")))
        
        logger.info("Collecting JavaScript errors")
        logs = driver.get_log('browser')
        js_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        logger.info("Checking for specific elements")
        try:
            header = driver.find_element("tag name", "header")
            nav = driver.find_element("tag name", "nav")
            main = driver.find_element("tag name", "main")
            logger.info("We have a basic structure!")
        except Exception as e:
            logger.warning(f"Missing basic structure: {str(e)}")
            js_errors.append({"message": f"Missing basic structure: {str(e)}"})
        
        if js_errors:
            logger.warning(f"Found {len(js_errors)} JavaScript errors")
        else:
            logger.info("No JavaScript errors found")
        
        return js_errors
    except Exception as e:
        logger.error(f"Selenium test error: {str(e)}")
        return [{"message": f"Selenium test error: {str(e)}"}]

def main():
    logger.info("Starting CRM improvement process")
    requirements = """
    Implement a CRM application for Klarna with the following features:
    1. Main HTML structure with a header, navigation, and main content area.
    2. Beautiful design using Klarna colors and logo (https://images.ctfassets.net/4pxjo1vaz7xk/21WIRpMQF4x4yzTUsDj1qy/691272c0a3cc22306c06f8d5e37da596/DAT-Wordmark_Pink_And_Black.webp?w=2048&q=75).
    3. Color scheme using rgb(11, 5, 29) and rgb(255, 168, 205).
    4. JavaScript object to serve as the 'database' for leads, accounts, and opportunities.
    5. Leads index view with a table displaying leads.
    6. Simple dashboard with key metrics.
    7. Lead management functionality (add, edit, delete, view leads).
    8. Account management features (add, edit, delete, view accounts).
    9. Contact management system within accounts.
    10. Opportunity management with a simple pipeline view.
    11. Task and activity management.
    12. Simple search functionality across leads, accounts, and opportunities.
    13. Single page application functionality where views update based on navigation without page reload.
    """

    max_iterations = 20 # this is so you don't run forever or blow tokens
    iteration_count = 0 
    delay = 10  # delay between iterations in seconds

    logger.info("Setting up selenium...")
    driver = setup_selenium()

    while iteration_count < max_iterations:
        logger.info(f"Starting iteration {iteration_count + 1} of {max_iterations}")
        
        existing_html = get_file_content('index.html')
        existing_js = get_file_content('app.js')
        existing_css = get_file_content('styles.css')

        logger.info("Running Selenium tests")
        js_errors = run_selenium_tests(driver)

		# give ai some context
        context = (
            f"Current 'index.html' content:\n{existing_html}\n\n"
            f"Current 'app.js' content:\n{existing_js}\n\n"
            f"Current 'styles.css' content:\n{existing_css}\n\n"
            f"JavaScript errors:\n{json.dumps(js_errors, indent=2)}\n\n"
        )

        prompt = (
            f"You are improving a CRM application for Klarna. Here are the full requirements:\n\n"
            f"{requirements}\n\n"
            "Based on the current state of the application, these requirements, and the JavaScript errors, decide what to improve or implement next. "
            "Focus on making meaningful progress towards completing all requirements and fixing any errors.\n\n"
            "Requirements:\n"
            "1. Use only HTML, CSS, and JavaScript.\n"
            "2. Ensure the code is well-structured and follows best practices.\n"
            "3. Implement features in a modular and scalable way.\n"
            "4. Use a global JS object to store data (as a prototype).\n"
            "5. Ensure the application remains functional after each update.\n"
            "6. Address any JavaScript errors reported by Selenium.\n\n"
            "Instructions:\n"
            "Generate JSON command(s) to update 'index.html', 'app.js', and/or 'styles.css'. Each command should replace the entire content of the file.\n\n"
            "The JSON command(s) should follow this format:\n"
            "[\n"
            "  {\n"
            '    "action": "update_file",\n'
            '    "filename": "index.html",\n'
            '    "content": "entire file content here"\n'
            "  },\n"
            "  {\n"
            '    "action": "update_file",\n'
            '    "filename": "app.js",\n'
            '    "content": "entire file content here"\n'
            "  },\n"
            "  {\n"
            '    "action": "update_file",\n'
            '    "filename": "styles.css",\n'
            '    "content": "entire file content here"\n'
            "  }\n"
            "]\n\n"
            "Return only the JSON command(s) without any additional text. This is extremely important for the script to work correctly and if you don't it will fail. I will also lose my job and the Klarna CEO will be very upset. RETURN ONLY JSON COMMANDS!\n\n"
        )

        logger.info("Improving your app...")
        commands = get_command_from_openai(prompt, context)
        if commands:
            logger.info(f"Received {len(commands)} command")
            for command in commands:
                execute_command(command)
        else:
            logger.warning(f"No valid commands received for iteration{iteration_count + 1}. Skipping.")

        iteration_count += 1
        logger.info(f"Completed iteration {iteration_count} of {max_iterations}")
        
        logger.info(f"Waiting for {delay} seconds before next iteration")
        time.sleep(delay)

    logger.info("Script completed all iterations")
    
    logger.info("Closing Selenium...")
    driver.quit()

if __name__ == "__main__":
    main()