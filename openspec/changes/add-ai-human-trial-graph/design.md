# Design

The existing AI-vs-AI graph remains unchanged. A separate interactive graph
shares case helpers, prompt builders, transcript models, and witness nodes.
Human attorney nodes interrupt for base64 audio; Deepgram converts audio to
transcript text before the graph appends a normal transcript turn.
