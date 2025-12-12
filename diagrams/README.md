# MLOps Architecture Diagrams

This folder contains Mermaid diagrams illustrating the production-ready MLOps architecture on GCP.

## Diagram Files

### System Architecture

1. **overall-architecture.mmd** - Complete system overview showing GitHub, Cloud Build CI/CD, and multi-environment GCP projects (dev/test/prod)

2. **multi-environment.mmd** - Multi-environment promotion strategy (dev → test → prod)

3. **infrastructure-terraform.mmd** - Terraform modules and GCP resources provisioned per environment

### ML Pipelines

4. **training-pipeline.mmd** - Training pipeline architecture from data preprocessing to model registry

5. **prediction-pipeline.mmd** - Batch prediction pipeline with model monitoring and skew detection

6. **component-interaction.mmd** - How the 8 reusable Kubeflow components interact with pipelines and GCP services

### Workflows

7. **cicd-pipeline-flow.mmd** - Complete CI/CD workflow from code commit to deployment

8. **training-sequence.mmd** - Sequence diagram showing step-by-step training pipeline execution

9. **prediction-sequence.mmd** - Sequence diagram for prediction pipeline workflow

## How to View

These Mermaid diagrams can be rendered using:

### GitHub
Simply view the `.mmd` files in GitHub - they render automatically.

### VS Code
Install the [Mermaid Preview Extension](https://marketplace.visualstudio.com/items?itemName=vstirbu.vscode-mermaid-preview)

### Online Editors
- [Mermaid Live Editor](https://mermaid.live/)
- Copy/paste the content of any `.mmd` file

### Documentation Tools
- **MkDocs**: Use [mkdocs-mermaid2-plugin](https://github.com/fralau/mkdocs-mermaid2-plugin)
- **GitBook**: Native Mermaid support
- **Confluence**: Use Mermaid macro or plugins

### Command Line
```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Convert to PNG
mmdc -i overall-architecture.mmd -o overall-architecture.png

# Convert to SVG
mmdc -i training-pipeline.mmd -o training-pipeline.svg

# Convert all diagrams
for file in *.mmd; do mmdc -i "$file" -o "${file%.mmd}.png"; done
```

## Color Scheme

The diagrams use Google Cloud brand colors:
- **Blue (#4285f4)**: Cloud Build, general services
- **Green (#34a853)**: Dev environment, successful operations
- **Yellow (#fbbc04)**: Test environment, warnings
- **Red (#ea4335)**: Prod environment, critical components
- **Orange (#ff6d00)**: Alerts

## Diagram Descriptions

### overall-architecture.mmd
Shows the complete MLOps ecosystem including:
- GitHub repository with PRs and releases
- Cloud Build triggers (6 CI/CD pipelines)
- Three GCP environments (dev/test/prod)
- Key services: Artifact Registry, Vertex AI, BigQuery, GCS, Model Registry

### training-pipeline.mmd
Illustrates the ML training workflow:
- Data preprocessing in BigQuery
- Train/validation/test split to GCS
- Hyperparameter tuning with Vertex AI
- Custom TensorFlow training container
- Champion vs challenger model comparison
- Model registry upload

### prediction-pipeline.mmd
Shows batch prediction process:
- Champion model lookup from registry
- Data preprocessing
- Batch prediction job
- Model monitoring with skew detection
- Email alerts for data drift

### cicd-pipeline-flow.mmd
Complete developer workflow:
- Feature branch → PR → validation
- Pre-commit hooks and unit tests
- E2E testing (manual trigger)
- Terraform planning
- Merge → infrastructure deployment
- Git tag → release → container build
- Pipeline scheduling to test/prod

### training-sequence.mmd
Step-by-step sequence showing:
- Release creation and pipeline publishing
- Schedule creation via Cloud Build
- Data extraction and preprocessing
- Hyperparameter tuning execution
- Model training and evaluation
- Champion model selection logic

### prediction-sequence.mmd
Prediction workflow sequence:
- Cloud Run function trigger
- Model lookup
- Data preprocessing
- Batch prediction execution
- Monitoring and skew detection
- Pub/Sub notification

### infrastructure-terraform.mmd
Terraform resources deployed:
- vertex_deployment module
- cloudrunfunction module
- Service accounts and IAM roles
- GCS buckets
- Artifact Registry repositories
- Metadata store
- Pub/Sub topics

### component-interaction.mmd
Shows how 8 reusable components are used:
- Training pipeline uses 6 components
- Prediction pipeline uses 3 components
- Integration with BigQuery, GCS, Vertex AI, Model Registry

### multi-environment.mmd
Environment promotion strategy:
- Code flows: Feature → Main
- Infrastructure: Terraform applies to all environments
- Pipelines: Released to all, promoted through validation
- Models: Experiments (dev) → Validation (test) → Champions (prod)

## Contributing

When adding new diagrams:
1. Create a `.mmd` file with descriptive name
2. Use the established color scheme
3. Add description to this README
4. Keep diagrams focused on a single aspect
5. Use comments in the diagram for complex logic

## References

- [Mermaid Documentation](https://mermaid.js.org/)
- [Mermaid Syntax](https://mermaid.js.org/intro/syntax-reference.html)
- [Graph/Flowchart Syntax](https://mermaid.js.org/syntax/flowchart.html)
- [Sequence Diagram Syntax](https://mermaid.js.org/syntax/sequenceDiagram.html)
