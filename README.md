# u(micro)Bridge

An incredibly minimal IRC <--> Disord bridge written in std python. Dogfood.

Channels are 1:1, Bridge(s) and Server(s) are 1:1.

Configuration
----
ubridge uses a config located [at] `config.json`, an example is provided [at] `config.def.json`.

Usage
----
The script is located [at] `main.py`

Caveats
----
- ubridge should deafen its puppet irc accounts to channel messages. This user mode is non-standard, and so will have to be changed from server-to-server. The relevant line is within irc.py: `irc_.create_user()`.
- discord does not (to my knowledge) allow for notifications awaiting new messages; this means that ubridge has to poll a channel for new messages. The time between each poll is set as the 'refresh' variable in config.json.
