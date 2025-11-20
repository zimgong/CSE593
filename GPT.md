We are working on a HCI project of effortless mobile communication in multi-language or slang contexts which satisfies the need for text entry on a mobile phone to be accurate and fast, no matter the language or slang used. While autocorrect features may assist in correcting typos and misspellings, it can also be a hindrance when it gives incorrect suggestions. To attempt to solve this issue, we generated a diverse set of user requirements, ultimately informing the creation of an initial design and paper prototype of ``CONTEXT GENIE'', a feature that can be added to mobile texting apps. 

We propose the following user requirements:

- Users need their intended meaning to be communicated without distortion when the message is sent.   
- Users need to be able to adjust their language in a manner appropriate to the recipient’s language and relationship without disrupting their typing flow.
- Users should observe fewer unintended spelling and grammar errors during message composition and fix them faster than manual typing or standard autocorrect.
- Final user texts should match their preferred style in formality, tone, etc., appropriate to the recipient and context.
- Users should be able to input in multiple languages, including in multiple scripts or transliterations, in their message while maintaining the intended meaning without interference.
- Users must be able to type in informal, slang, or abbreviated language as intended while preserving the meaning of their message.
- Users need to be comfortable with the level of automatic text modification with minimal manual override.
- Users need to feel confident that their spelling or grammar is appropriate for the intended context.

We also propose the following low-fidelity prototype:

The prototype should have a similar interface to the iOS suggestion system. Every implementation has a mixture of suggestions in this interface, with varying tones or languages. It should highlight to distinguish different languages, especially for words spelled the same but with different meanings across multiple languages. A button should be provided to customize the suggestions (by pulling up a menu) directly in the suggestion bar.

The technical stack behind the suggestion system, in which information about the conversation, the recipient, and the words being typed are fed into an LLM, which outputs suggestions and corrections. 

In the selection menu, provide sliders to customize the rate at which the system overrides suggestions to fit the tone, language, and formality of the conversation. Try also to indicate the level of formality that the keyboard's recommendations are tailored to. 

Your task is to create a high-fidelity prototype of the following features:

- A keyboard layout with a GENIE button to toggle the GENIE feature on and off, and double-tapping the GENIE button to open the GENIE menu.
- A GENIE menu with a slider to customize the rate at which the system overrides suggestions to fit the tone, language, and formality of the conversation.
- A autocorrect/suggestion interface to display the suggestions and corrections.
- Possiblity to override directly when the slider is on aggressive mode. 
- Do not override suggestions when the slider is on passive mode.
- Use LLM to provide suggestions and corrections. 
- Try supporting multiple languages and scripts.
- Try supporting informal, slang, or abbreviated language as intended. 
- Try supporting transliterations.

Please refer to the sketches and paper prototype under the media folder for reference.

Also create a control group prototype which resembles the existing autocorrect/suggestion interface.
