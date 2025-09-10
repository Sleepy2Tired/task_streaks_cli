# task_streaks_cli
A command-line tool to track daily tasks and compute streaks.

## Features
- Track daily tasks with ease
- Mark tasks as done
- Compute current and best streaks
- Display a mini calendar view of your tasks

## Quickstart
To get started with `task_streaks_cli`, follow these steps:

1. **Install** the tool:
   ```bash
   pip install task_streaks_cli
   ```

2. **Run** the application:
   ```bash
   task_streaks_cli
   ```

## Usage Examples
- **Add a new task:**
  ```bash
  task_streaks_cli add "Read a book"
  ```

- **Mark a task as done:**
  ```bash
  task_streaks_cli done "Read a book"
  ```

- **View current streak:**
  ```bash
  task_streaks_cli streak
  ```

- **Display mini calendar:**
  ```bash
  task_streaks_cli calendar
  ```

## Configuration
You can customize the configuration by editing the `config.yaml` file located in the home directory. Key settings include:
- Task reminder intervals
- Streak notification preferences

## Roadmap
- [ ] Implement task categorization
- [ ] Add user authentication
- [ ] Enhance calendar visualizations
- [ ] Introduce analytics for task completion

## FAQ
**Q: Can I reset my streak?**  
A: Yes, you can reset your streak using the command `task_streaks_cli reset`.

**Q: Is there a way to view completed tasks?**  
A: Yes, use the command `task_streaks_cli completed` to view all completed tasks.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.