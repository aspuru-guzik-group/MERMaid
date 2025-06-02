# Guide on Customizing MERMaid

MERMaid can be adapted to different domains or tasks with minimal effort. 
This guide outlines how to modify MERMaid for:

- **Domain-level adaptation**: Using MERMaid for a new chemical domain (e.g., non-electrochemical reactions) while performing the same task (reaction mining).
- **Task-level adaptation**: Using MERMaid for a different task (e.g., substrate scope extraction instead of optimization tables).

---

## 1. Domain-Level Adaptation  
*Applying MERMaid to a different chemical domain for the same task of reaction mining.*

### 1.1 Modifications for `DataRaider`

**File to edit**: `scripts/startup.json`

- **Option 1: Use inbuilt reaction parameters**  
  A set of 22 common reaction parameters is provided in `Prompts/inbuilt_keyvaluepairs.txt`.  
  To use them, include the desired keys in the `"keys"` field of `startup.json`.

  **Example:**
  ```json
  "keys": ["Entry", "Anode", "Cathode", "Electrolytes", "Solvents", "Duration"]

- **Option 2: Add custom reaction parameters**  
  You can define new keys directly in `startup.json` using the format: 
  `"<custom_key>" : "<brief description>"
  
  **Example:**
  ```json
  "flow rate": "flow rate of electrolyte solution (mL/min)"

> All selected and user-defined keys are automatically injected into the base prompt and reflected in downstream logic. No code-level changes are needed.

### 1.2 Modifications for `KGWizard`
(To be added)

## 2. Task-Level Adaptation 
*Applying MERMaid to a different task such as substrate scope analysis*
> Task-level adaptation will require some **prompt engineering** if the new task significantly deviates from the original one of reaction mining from optimization studies.

### 2.1 Modifications for `DataRaider`
1. **Update the filter prompt**  
   File: `Prompts/filter_image_prompt.txt`  
   Change the filtering question to match your new task. For example, you can change to: 
   ```
   Does the figure contain substrate scope of a reaction?
   ```
   *Optional:* Update the associated key `is_optimization_table: true` in `startup.json` for labeling consistency. For example, you can change to `is_substrate_scope: true`. 

2. **Edit the reaction parameter keys**
Use the same approach as in 1.1. 

3. **Modify the base prompt**
File: `Prompts/base_prompt.txt`
Update this prompt to:
- Reflect the expected output structure for your task
- Redefine the dictionaries you want to extract
- Adjust the parsing rules accordingly

### 2.2 Modifications for `KGWizard`
(To be added)