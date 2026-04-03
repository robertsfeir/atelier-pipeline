# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Older releases | No |

Only the latest release receives security fixes. Please upgrade before
reporting issues against older versions.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Send your report to: **robert@sfeir.dev**

Include the following in your report:

- **Description:** A clear summary of the vulnerability.
- **Reproduction steps:** Detailed steps to reproduce the issue.
- **Affected component:** Which part of the system is impacted (hooks,
  brain MCP server, agent constraints, plugin scripts, etc.).
- **Impact assessment:** Your understanding of the severity and potential
  exploitation.

### Response Timeline

- **48 hours:** Acknowledgment of your report.
- **7 days:** Status update with an initial assessment and next steps.
- **Coordinated disclosure:** We will work with you on a timeline for public
  disclosure once a fix is available.

## Scope

### In Scope

- Hook enforcement bypasses (PreToolUse hooks that fail to block unauthorized
  operations)
- Brain MCP server vulnerabilities (authentication, authorization, data
  exposure in the Node.js server or PostgreSQL layer)
- Prompt injection that bypasses agent constraints (circumventing mechanical
  enforcement of agent boundaries)
- Plugin script issues (setup scripts, lifecycle scripts that introduce
  security risks)

### Out of Scope

- Vulnerabilities in upstream dependencies (report these to the respective
  projects directly)
- Attacks requiring physical access to the machine
- Social engineering attacks against maintainers or contributors

## Credit

With your permission, we will credit security reporters in the project
changelog. Let us know in your report how you would like to be attributed
(name, handle, or anonymous).
