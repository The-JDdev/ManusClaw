<div align="center">

<img src="https://img.shields.io/badge/MOVED-Permanently-FF0000?style=for-the-badge&logo=github&logoColor=white" alt="MOVED">
<img src="https://img.shields.io/badge/ManusClaw-v5.0.0-ff69b4?style=for-the-badge&logo=github&logoColor=white" alt="Version">
<img src="https://img.shields.io/badge/New_Home-ManusClawAI-6C63FF?style=for-the-badge&logo=rocket&logoColor=white" alt="New Home">

<br><br><br>

# THIS REPOSITORY HAS MOVED

<br>

```
   ╔══════════════════════════════════════════════════════════╗
   ║                                                          ║
   ║     ██████╗ ██████╗  █████╗ ███╗   ██╗██╗███████╗       ║
   ║     ██╔══██╗██╔══██╗██╔══██╗████╗  ██║██║██╔════╝       ║
   ║     ██████╔╝██████╔╝███████║██╔██╗ ██║██║███████╗       ║
   ║     ██╔═══╝ ██╔══██╗██╔══██║██║╚██╗██║██║╚════██║       ║
   ║     ██║     ██║  ██║██║  ██║██║ ╚████║██║███████║       ║
   ║     ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚══════╝       ║
   ║                   Claws of Intelligence                  ║
   ║                                                          ║
   ║     has evolved — and so has its home.                   ║
   ║                                                          ║
   ╚══════════════════════════════════════════════════════════╝
```

<br>

</div>

---

## The ManusClaw project has a new permanent home.

This repository is **no longer the active source code repository** for ManusClaw. The entire codebase — every line, every feature, every test — has been **permanently migrated** to a dedicated organization repository under **ManusClawAI**.

### Where is ManusClaw now?

<table>
<tr>
<td>

<a href="https://github.com/ManusClawAI/manusclaw">
<img src="https://img.shields.io/badge/GO_HERE-ManusClawAI%2Fmanusclaw-181717?style=for-the-badge&logo=github&logoColor=white" alt="New Repository">
</a>

</td>
</tr>
</table>

<br>

> **`https://github.com/ManusClawAI/manusclaw`**
> *This is the new canonical home of the ManusClaw autonomous AI agent framework.*

---

<br>

### What happened?

ManusClaw started as a personal project in a single developer's GitHub account. It grew — from a simple CLI agent into a production-grade omnichannel AI platform with 14+ feature categories, 210 passing tests, 12+ messaging channels, voice I/O, SSH gateway, webhooks, multi-agent orchestration, and a thriving community.

That kind of growth demands a proper home. **ManusClawAI** is that home — a dedicated GitHub organization built to house the framework's present and future. The migration ensures long-term stability, better collaboration tooling, proper team management, and a clean separation between the **project** (ManusClawAI) and the **creator** (The-JDdev).

### What changed?

| Aspect | Before (This Repo) | After (New Repo) |
|--------|---------------------|-------------------|
| **Owner** | `The-JDdev` (personal account) | `ManusClawAI` (organization) |
| **URL** | `github.com/The-JDdev/manusclaw` | `github.com/ManusClawAI/manusclaw` |
| **Status** | **Archived — read-only redirect** | **Active — all development here** |
| **Issues & PRs** | Closed | Open at [ManusClawAI/manusclaw](https://github.com/ManusClawAI/manusclaw/issues) |
| **Releases** | Frozen | Published at [ManusClawAI/manusclaw/releases](https://github.com/ManusClawAI/manusclaw/releases) |
| **Stars & Forks** | Preserved for history | Fresh start at [ManusClawAI/manusclaw](https://github.com/ManusClawAI/manusclaw) |

### What you should do right now

**If you have this repo cloned locally:**
```bash
# Remove the old clone
rm -rf manusclaw

# Clone from the new home
git clone https://github.com/ManusClawAI/manusclaw.git
cd manusclaw

# Install (same as before — nothing changes)
pip install -e ".[all-plus]"
```

**If you have a fork of this repo:**
```bash
# Add the new upstream
cd your-fork
git remote add upstream https://github.com/ManusClawAI/manusclaw.git
git fetch upstream
git checkout main
git reset --hard upstream/main
git push origin main --force
```

**If you referenced this repo in documentation, CI/CD, or dockerfiles:**
```bash
# Find all old references
rg "The-JDdev/manusclaw" --type md --type yaml --type yml --type toml --type sh --type Dockerfile

# Replace them everywhere
find . -type f \( -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.toml" -o -name "*.sh" -o -name "Dockerfile" \) \
  -exec sed -i 's|The-JDdev/manusclaw|ManusClawAI/manusclaw|g' {} +
```

**If you depend on this repo via `requirements.txt` or `pyproject.toml`:**
```
# OLD (will stop receiving updates)
manusclaw @ git+https://github.com/The-JDdev/manusclaw.git@main

# NEW (active development)
manusclaw @ git+https://github.com/ManusClawAI/manusclaw.git@main
```

---

<br>

### The Ecosystem

ManusClaw is now a multi-repository ecosystem:

| Repository | URL | Purpose |
|------------|-----|---------|
| **Core Engine** | [`ManusClawAI/manusclaw`](https://github.com/ManusClawAI/manusclaw) | Source code — the agent framework itself |
| **Setup & Docs** | [`The-JDdev/manusclaw-setup`](https://github.com/The-JDdev/manusclaw-setup) | Installation guides, configuration reference, platform tutorials |

> **Setup guide**: For the complete production-grade setup and usage documentation, visit [The-JDdev/manusclaw-setup](https://github.com/The-JDdev/manusclaw-setup).

---

<br>

### Why the move?

This isn't just a URL change. It's an evolution:

1. **Organizational Identity** — ManusClaw is no longer a side project. It's a framework with a community, a roadmap, and a future. It deserves an organizational home, not a personal folder.

2. **Collaboration** — An organization repository enables proper team management, CODEOWNERS files, branch protection rules, and structured contribution workflows that a personal account cannot provide.

3. **Separation of Concerns** — The creator's personal GitHub (`The-JDdev`) remains personal. The framework's home (`ManusClawAI`) is professional and project-focused. This separation benefits both the project and the developer.

4. **Future-Proofing** — As ManusClaw grows toward v6.0, additional repositories may be created under the `ManusClawAI` org: plugins, marketplace, benchmarks, and more. The organization structure makes this possible.

---

<br>

### Frequently Asked Questions

**Q: Will this repo still receive updates?**
**A:** No. This repository is permanently archived. All future development — bug fixes, features, releases — happens exclusively at [`ManusClawAI/manusclaw`](https://github.com/ManusClawAI/manusclaw).

**Q: Are my old commits and history preserved?**
**A:** Yes. The full git history has been migrated to the new repository. Every commit, every contributor, every milestone is preserved.

**Q: What about issues and pull requests?**
**A:** All open issues and PRs from this repo were reviewed during migration. Any that are still relevant should be reopened at [`ManusClawAI/manusclaw/issues`](https://github.com/ManusClawAI/manusclaw/issues).

**Q: My CI/CD pipeline points to this repo. Will it break?**
**A:** Not immediately — the code still exists here. But it will become stale. Update your pipelines to point to `ManusClawAI/manusclaw` as soon as possible.

**Q: Who is "ManusClawAI"?**
**A:** ManusClawAI is the GitHub organization created specifically for the ManusClaw project. It is owned and maintained by The-JDdev (SHS Lab), the original creator.

**Q: Can I still contact the developer?**
**A:** Absolutely. The-JDdev can be reached at:
- GitHub: [The-JDdev](https://github.com/The-JDdev)
- Telegram: [@singularityos](https://t.me/singularityos)
- Email: [thejddev.official@gmail.com](mailto:thejddev.official@gmail.com)
- Facebook: [itsshsshobuj](https://facebook.com/itsshsshobuj)

---

<br>

<div align="center">

```
  FROM                          TO
  ──────────────────────────    ──────────────────────────
  github.com/The-JDdev/         github.com/ManusClawAI/
  manusclaw                     manusclaw

  The past.                     The future.
  Thank you for everything.     We're just getting started.
```

<br>

<a href="https://github.com/ManusClawAI/manusclaw">
<img src="https://img.shields.io/badge/MIGRATE_NOW-Click_Here-00C853?style=for-the-badge&logo=github&logoColor=white&labelColor=181717" alt="Migrate Now">
</a>

<br><br>

<img src="https://img.shields.io/badge/Built_by-The--JDdev_(SHS_Lab)-6C63FF?style=for-the-badge" alt="Developer">

**ManusClaw — Claws of Intelligence**

</div>
