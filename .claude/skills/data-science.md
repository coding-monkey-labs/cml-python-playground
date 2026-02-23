# Skill: Data Science & Notebooks

## Capability

Data processing, analysis, visualization, and Jupyter notebook operations.

## Tools Used

- **Bash** — run scripts, install data packages, launch Jupyter
- **NotebookEdit** — create and edit Jupyter notebook cells
- **Read** — inspect notebook content and data files
- **Write** — create data processing scripts

## Patterns

### Notebook Operations
```python
# NotebookEdit tool for cell manipulation
# cell_type: "code" or "markdown"
# edit_mode: "replace", "insert", "delete"
```

### Common Data Stack
```bash
uv pip install pandas numpy matplotlib seaborn jupyter
```

### Quick Data Exploration
```python
import pandas as pd
df = pd.read_csv("data.csv")
print(df.shape, df.dtypes)
df.describe()
```

### Visualization
```python
import matplotlib.pyplot as plt
df.plot(kind="bar", x="category", y="value")
plt.tight_layout()
plt.savefig("output.png")
```

## Conventions

- pandas for tabular data, numpy for numerical
- matplotlib/seaborn for visualization
- Keep notebooks focused — one analysis per notebook
- Extract reusable logic into .py modules
- Save figures as files, don't rely on inline display

## Background Agent Usage

- Background data processing for large datasets
- Parallel notebook cell execution for independent analyses
- Background package installation while setting up notebooks
