# Data Schema

## Columns

| Column | Type | Description |
|---|---|---|
| ID | Integer | Unique identifier for the agent |
| Type | String | One of: Internet, Firewall, Server, User, PC, Mobile |
| Awareness | Float | 0.0-1.0, Security awareness level (Users only) |
| AV | Float | 0.0-1.0, Antivirus strength |
| Patch | Float | 0.0-1.0, Patch level |
| Port | Float | 0.0-1.0, Port vulnerability (higher is safer?) or open ports? TBD |
| Value | Float | Monetary value of asset |
| ConnectedTo | String | Semicolon-separated list of IDs this agent connects to |
