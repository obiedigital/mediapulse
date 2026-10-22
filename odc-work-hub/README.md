# ODC Work Hub

A single-page tracker for ODC work: tasks, team, KPIs across the nine annual objectives, and weekly reports.

**Hosted version (shared, live):** https://claude.ai/artifact/TbhLkLxTk88TykrCVr6p4p
Data there is stored in the artifact's shared database, so anyone you share the page with as Contributor or Editor sees and edits the same tasks.

**Local version:** open `odc_work_hub.html` in a browser. Data is saved in that browser only (localStorage). Use *Export backup* / *Import backup* on the Overview tab to move data between the two.

## What it does

| Tab | Purpose |
|---|---|
| Overview | Open / due / blocked / overdue counts, KPI scorecard, items needing attention, team load, backup and export |
| Tasks | Add, edit, filter (objective, owner, status, priority) and search tasks. Each task carries an ODC objective, owner, due date, priority, outcome (for Wins) and waiting-on / impact (for Blockers) |
| KPIs | Per-objective weight, target and actual. Progress uses the target when set, otherwise task completion. Overall score is weighted |
| Team | Workload per person, links to their tasks and their own report |
| Report | Wins, Blockers and Next Steps for a period and person, max 5 bullets each, every Win and Blocker tagged `[Obj N – Name]` or `[Unweighted / off-KPI]`. Copy, download as Markdown, or polish the wording with Claude (hosted version) |

## ODC objectives

1 Strategy & Governance · 2 Trainings · 3 Partnerships · 4 Projects · 5 Reporting · 6 Visibility · 7 Digitalisation · 8 Team Management · 9 Transformation
