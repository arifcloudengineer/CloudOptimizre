# CloudOptimizer — Roadmap (as-built)

| Phase | Status | Notes |
|---|---|---|
| 0 — Planning | ✅ | This doc + ProjectRequirements.md |
| 1 — Architecture | ✅ | Architecture.md (ASCII, no .drawio — see note below) |
| 2 — Repo structure | ✅ | See tree in root README |
| 3 — Terraform infra | ✅ | modules: iam, lambda, dynamodb, eventbridge, sns, s3 |
| 4 — Auth (IAM) | ✅ | Least-privilege policy in `modules/iam` |
| 5 — Cost scanner | ✅ | EC2, EBS, EIP, S3, RDS, ELB, NAT scanners |
| 6 — Recommendation engine | ✅ | `backend/recommender/engine.py` (condition → action → risk rules) |
| 7 — Savings calculator | ✅ | Static pricing table, `pricing_engine.py` |
| 8 — DB design | ✅ | See schema in Architecture.md / `models/schemas.py` |
| 9 — REST API | ✅ | FastAPI, see `backend/api/main.py` |
| 10 — React dashboard | ✅ | Dashboard, Resources, Recommendations pages |
| 11 — Scheduler | ✅ | EventBridge rule, daily by default (`terraform.tfvars`) |
| 12 — Notifications | ✅ | SNS, threshold-based in `notifier.py` |
| 13 — GitHub Actions | ✅ | `.github/workflows/ci-cd.yml` |
| 14 — Testing | ✅ | pytest for recommender + pricing + scanners (mocked boto3) |
| 15 — Documentation | ✅ | This file + root README |

**Note on architecture diagrams:** the original roadmap calls for `.drawio` files.
Those are binary/XML editor files that don't render usefully outside draw.io, so
this build uses a Mermaid diagram + ASCII flow in `Architecture.md` instead —
paste the Mermaid block into https://mermaid.live if you want an exportable
image, or recreate it in draw.io for your portfolio screenshots.

## Suggested next steps for you (not built in this pass)
1. Deploy `terraform apply` to a sandbox AWS account (see root README "Deploy").
2. Run one real scan against your own account, screenshot the dashboard.
3. Wire up the live AWS Cost Explorer API for the "How much am I spending?"
   dashboard card — this build estimates *waste*, not total spend.
4. Swap static pricing for the live AWS Price List API if you want savings
   estimates to be accurate, not just directionally close.
5. Add multi-account scanning via AWS Organizations + cross-account IAM roles.
