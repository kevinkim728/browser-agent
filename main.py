# main.py
"""
Browser Automation Agent - Chainlit Interface

Main entry point for the Chainlit web interface.
"""

import chainlit as cl
from agents import Runner, trace
from browser_agent_final import browser_agent, browser_session, AgentConfig
import os
import signal

@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    welcome_message = """

**BROWSER AGENT**    

**How to use:**
Just tell me what you want to do in plain English!

*Examples:*
- "Go to Amazon and search for the cheapest wireless headphones"
- "Navigate to Google and find the weather for New York"
- "Extract product prices from the search results"  

What would you like me to help you with?
"""
    actions = [
        cl.Action(name="Close Browser", payload={"action": "close"}, description="Close Browser Session"),
        cl.Action(name="Stop Session", payload={"action": "stop"}, description="Stop & Cleanup")
    ]
    await cl.Message(content=welcome_message, author="Browser Agent", actions=actions).send()
 

@cl.action_callback("Close Browser")
async def on_action(action):
    """Handle the close browser action."""
    try:
        await browser_session.close()
        cl.user_session.set("browser_active", False)
        
        await cl.Message(
            content="🔒 **Browser session closed safely.** You can refresh the page to start a new session.", 
            author="Browser Agent"
        ).send()
    except Exception as e:
        await cl.Message(
            content=f"❌ **Error closing browser:** {str(e)}", 
            author="Browser Agent"
        ).send()

@cl.action_callback("Stop Session")
async def on_stop_action(action):
    """Handle the stop session action."""
    await stop()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages and run browser automation."""
    
    # Show initial progress
    progress_msg = cl.Message(
        content="🔄 **Starting browser automation...**", 
        author="Browser Agent"
    )
    await progress_msg.send()
    
    try:
        # Update progress with more detail
        progress_msg.content = """
🌐 **Browser agent is working on your task...**

*This may take a few moments while I:*
- Launch the browser
- Navigate to websites  
- Interact with page elements
- Complete your requested actions

Please wait..."""
        await progress_msg.update()
        
        # Run the browser agent
        with trace('Browser Automation Agent'):
            result = await Runner.run(
                browser_agent, 
                message.content, 
                max_turns=AgentConfig().max_turns
            )
        
        # Prepare final response
        response_content = f"""
✅ **Task Completed Successfully!**

**Result:** {result.final_output}

---
*💡 Tip: You can ask me to perform another task or take additional actions on the current page.*
"""
        actions = [
            cl.Action(name="Close Browser", payload={"action": "close"}, description="Close Browser Session"),
            cl.Action(name="Stop Session", payload={"action": "stop"}, description="🛑 Stop & Cleanup")
    ]

        final_msg = cl.Message(
            content=response_content,
            author="Browser Agent",
            actions=actions
        )
        
        await final_msg.send()
        
    except Exception as e:
        error_msg = f"""
❌ **An error occurred during automation:**

**Error:** {str(e)}

**What you can try:**
- Rephrase your request with more specific details
- Check if the website is accessible
- Try a simpler action first (like navigating to a website)

Feel free to try again with a different approach!
"""
        actions = [
            cl.Action(name="Close Browser", payload={"action": "close"}, description="Close Browser Session"),
            cl.Action(name="Stop Session", payload={"action": "stop"}, description="🛑 Stop & Cleanup")
    ]
        await cl.Message(content=error_msg, author="Browser Agent", actions=actions).send()


@cl.on_stop
async def stop():
    """Clean up when the chat session ends and stop the app."""
    try:
        await browser_session.close()
        await cl.Message(
            content="🔒 **Browser session closed safely.** Thanks for using Browser Agent!", 
            author="Browser Agent"
        ).send()
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        os.kill(os.getpid(), signal.SIGINT)


if __name__ == "__main__":
    cl.run()
