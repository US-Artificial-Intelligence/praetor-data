# Praetor

Praetor is a dataset exploration tool. It is made for LLM finetuning data and prompts.

## About

Praetor is a super lightweight finetuning data and prompt management tool. The setup requirements are minimal, and so is the complexity.

In general, the system works like this: you start with a Project. A project has associated with it some prompt styles, which define format strings for the prompts. You can then add prompts in a particular style and then one or more completions to those prompts. When you're done editing prompts or completions, you can export that data in a json format. You can also import data in the same format.

Thus the hierarchy goes:

```
Projects --> Styles --> Prompts --> Completions
```

