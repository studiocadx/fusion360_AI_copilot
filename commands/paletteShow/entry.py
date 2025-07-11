import json
import adsk.core
import os
from ...lib import fusionAddInUtils as futil
from ...lib.ai_service import AIService
from ...lib.ai_modeling_actions import AIModelingActions
from ... import config
from datetime import datetime

app = adsk.core.Application.get()
ui = app.userInterface

# TODO ********************* Change these names *********************
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_PalleteShow'
CMD_NAME = 'CadxStudio AI Copilot'
CMD_Description = 'CadxStudio AI-powered natural language interface for Fusion 360'
PALETTE_NAME = 'CadxStudio AI Copilot for Fusion 360'
IS_PROMOTED = True

# Using "global" variables by referencing values from /config.py
PALETTE_ID = config.sample_palette_id

# Specify the full path to the local html. You can also use a web URL
# such as 'https://www.autodesk.com/'
PALETTE_URL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'html', 'index.html')

# The path function builds a valid OS path. This fixes it to be a valid local URL.
PALETTE_URL = PALETTE_URL.replace('\\', '/')

# Set a default docking behavior for the palette
PALETTE_DOCKING = adsk.core.PaletteDockingStates.PaletteDockStateRight

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

# Initialize AI service and modeling actions
ai_service = None
modeling_actions = None


# Executed when add-in is run.
def start():
    global ai_service, modeling_actions
    
    # Initialize AI service and modeling actions
    ai_service = AIService()
    modeling_actions = AIModelingActions()
    
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Add command created handler. The function passed here will be executed when the command is executed.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    palette = ui.palettes.itemById(PALETTE_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

    # Delete the Palette
    if palette:
        palette.deleteMe()


# Event handler that is called when the user clicks the command button in the UI.
# To have a dialog, you create the desired command inputs here. If you don't need
# a dialog, don't create any inputs and the execute event will be immediately fired.
# You also need to connect to any command related events here.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Command created event.')

    # Create the event handlers you will need for this instance of the command
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# Because no command inputs are being added in the command created event, the execute
# event is immediately fired.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Command execute event.')

    palettes = ui.palettes
    palette = palettes.itemById(PALETTE_ID)
    if palette is None:
        palette = palettes.add(
            id=PALETTE_ID,
            name=PALETTE_NAME,
            htmlFileURL=PALETTE_URL,
            isVisible=True,
            showCloseButton=True,
            isResizable=True,
            width=700,
            height=800,
            useNewWebBrowser=True
        )
        futil.add_handler(palette.closed, palette_closed)
        futil.add_handler(palette.navigatingURL, palette_navigating)
        futil.add_handler(palette.incomingFromHTML, palette_incoming)
        futil.log(f'{CMD_NAME}: Created a new palette: ID = {palette.id}, Name = {palette.name}')

    if palette.dockingState == adsk.core.PaletteDockingStates.PaletteDockStateFloating:
        palette.dockingState = PALETTE_DOCKING

    palette.isVisible = True


# Use this to handle a user closing your palette.
def palette_closed(args: adsk.core.UserInterfaceGeneralEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Palette was closed.')


# Use this to handle a user navigating to a new page in your palette.
def palette_navigating(args: adsk.core.NavigationEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Palette navigating event.')

    # Get the URL the user is navigating to:
    url = args.navigationURL

    log_msg = f"User is attempting to navigate to {url}\n"
    futil.log(log_msg, adsk.core.LogLevels.InfoLogLevel)

    # Check if url is an external site and open in user's default browser.
    if url.startswith("http"):
        args.launchExternally = True


# Use this to handle events sent from javascript in your palette.
def palette_incoming(html_args: adsk.core.HTMLEventArgs):
    global ai_service, modeling_actions
    
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Palette incoming event.')

    message_data: dict = json.loads(html_args.data)
    message_action = html_args.action

    log_msg = f"Event received from {html_args.firingEvent.sender.name}\n"
    log_msg += f"Action: {message_action}\n"
    log_msg += f"Data: {message_data}"
    futil.log(log_msg, adsk.core.LogLevels.InfoLogLevel)

    # Handle AI commands
    if message_action == 'aiCommand':
        try:
            user_command = message_data.get('command', '')
            session_id = message_data.get('sessionId', '')
            
            futil.log(f"Processing AI command: {user_command}")
            
            # Send processing status to UI
            palette = ui.palettes.itemById(PALETTE_ID)
            processing_response = {
                "status": "processing",
                "originalCommand": user_command,
                "message": "CadxStudio AI is analyzing your command..."
            }
            palette.sendInfoToHTML("aiResponse", json.dumps(processing_response))
            
            # Process the command with AI service
            ai_response = ai_service.process_natural_language_command(user_command)
            
            futil.log(f"AI Response: {json.dumps(ai_response)}")
            
            # If AI successfully parsed the command, execute it
            if ai_response.get("status") == "success" and ai_response.get("action"):
                execution_result = modeling_actions.execute_command(ai_response)
                
                # Merge AI response with execution result
                final_response = {
                    **ai_response,
                    **execution_result,
                    "originalCommand": user_command,
                    "sessionId": session_id
                }
            else:
                # AI couldn't parse the command or there was an error
                final_response = {
                    **ai_response,
                    "originalCommand": user_command,
                    "sessionId": session_id
                }
            
            # Send final response to UI
            palette.sendInfoToHTML("aiResponse", json.dumps(final_response))
            
            # Set return data for the HTML promise
            html_args.returnData = json.dumps(final_response)
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": f"System error: {str(e)}",
                "originalCommand": message_data.get('command', ''),
                "sessionId": message_data.get('sessionId', '')
            }
            
            futil.log(f"AI Command Error: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            
            # Send error to UI
            palette = ui.palettes.itemById(PALETTE_ID)
            palette.sendInfoToHTML("aiResponse", json.dumps(error_response))
            
            html_args.returnData = json.dumps(error_response)

    # Handle legacy message from palette (for backward compatibility)
    elif message_action == 'messageFromPalette':
        arg1 = message_data.get('arg1', 'arg1 not sent')
        arg2 = message_data.get('arg2', 'arg2 not sent')

        msg = 'An event has been fired from the html to Fusion with the following data:<br/>'
        msg += f'<b>Action</b>: {message_action}<br/><b>arg1</b>: {arg1}<br/><b>arg2</b>: {arg2}'               
        ui.messageBox(msg)
        
        # Return value for legacy compatibility
        now = datetime.now()
        currentTime = now.strftime('%H:%M:%S')
        html_args.returnData = f'OK - {currentTime}'
    
    else:
        # Unknown action
        html_args.returnData = f'Unknown action: {message_action}'


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME}: Command destroy event.')

    global local_handlers
    local_handlers = []