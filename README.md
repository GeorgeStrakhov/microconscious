# Microconscious

Microconscious is an experiment in trying to string together LLM calls across time to create minimal self-awareness.
The idea is simple: single LLM call represents a single thought. But concsicousness and self-awareness depend on the model of itself and its own state and continuation of intention.

So the idea is to create a self-awareness loop by calling the LLM with a prompt that asks it to describe its own state and then use the output as a prompt for the next LLM call.

We also need to think about interaction with the world. So we need to incorporate console input and output into the loop.

Our microconscious digital organism (MiDO) should have:

- an identity
- a goal
- a state
- a memory
- a way to interact with the world

For now let's keep it very simple and define our MiDO in a yaml file, where we can give it a name and a goal.

We can keep the state in a separate jsonl file, where we can store the state of the MiDO at each step.

We can also keep the memory in a separate jsonl file, where we can store the memory of the MiDO at each step.

For the interaction with the world - for now let's just have a simple console input and output.

Let's keep it simple and start with a single iteration of the loop:

1. Load the MiDO from the yaml file
2. Load the state from the jsonl file
3. Load the information from the input (just a console input I can give as a string)
4. Load the memory from the jsonl file (for now - the full thing, in the future - just the relevant memory based on state and input)
5. Make a call to the LLM that takes the MiDO, state, input (sensor / console) information and memory and returns an action. For now the only action is to print something to the console.
6. Make another call to the LLM that takes the MiDO, state, input (sensor / console) information and memory and the taken action and returns a new state and memory. This is the self-awareness loop / reflection.
7. Save the new state and memory to the jsonl files
8. End

(in the future this will be a loop that is triggered by the heartbeat of the MiDO)
