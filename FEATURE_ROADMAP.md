# Tkinter Notes App Feature Roadmap

This roadmap turns the current app into a more polished product that feels ready for real users and easier to sell.

## Current Strengths

- Task creation and deletion
- Priority and completion updates
- Due-date color highlighting
- Attachment linking
- Task summary popups
- CSV export

## Roadmap Overview

### Phase 1: Core Product Polish

These are the highest-impact changes because they make the app feel complete.

1. Full task editing - implemented
   - Added editing for task name, due date, time, duration, notes, priority, and completion status.
   - Replaced the limited update popup with a complete prefilled edit form.

2. Search, filter, and sort controls - implemented (archive filter pending)
   - Added filters for all, pending, completed, overdue, and due today.
   - Added sorting by due date, priority, creation date, and status.
   - Added quick filter for tasks with attachments.
   - Archived-item filter will be added after archive support is implemented.

3. Better layout and navigation - implemented
   - Added a top toolbar for primary actions.
   - Replaced scattered buttons with grouped controls.
   - Added titled panes and empty-state messages when no tasks or files exist.

4. Keyboard shortcuts
   - Add shortcuts for new task, search, edit, delete, export, and open summary.
   - Make the app faster for power users.

### Phase 2: Professional Workflow Features

These features make the app more useful for daily planning and retention.

1. Reminders and notifications
   - Let users set reminder times for tasks.
   - Show alerts when tasks are due soon or overdue.

2. Recurring tasks
   - Support repeating tasks daily, weekly, monthly, or custom.
   - Automatically generate the next instance after completion.

3. Tags and projects
   - Add tags such as Work, Personal, Study, or Client.
   - Allow filtering by tag or project.

4. Archive instead of hard delete
   - Move deleted tasks to an archive.
   - Add restore and permanent delete options.

5. Rich notes support
   - Support longer notes with better formatting.
   - Consider markdown-style formatting or a clean editor.

### Phase 3: Data Safety and Trust

These features reduce risk and make the app safer to buy and use.

1. Backup and restore
   - Export the full database to a backup file.
   - Restore from a backup in one click.

2. Import from CSV and database migration
   - Import tasks from CSV.
   - Support moving data from older versions of the app.

3. Undo support
   - Allow undo after delete, archive, and status changes.
   - Show a short toast or message for recovery.

4. Attachment management
   - Open attachments directly from the app.
   - Add remove attachment and preview support.
   - Support drag and drop attachment upload.

### Phase 4: Sales-Ready Product Experience

These features improve presentation, branding, and buyer confidence.

1. Dashboard and insights
   - Show task counts for today, this week, overdue, and completed.
   - Add simple charts or summary cards.

2. Branding and theming
   - Add a proper app icon and About dialog.
   - Choose a consistent theme and spacing system.
   - Make the interface feel intentional instead of default Tkinter.

3. Installer and packaging
   - Build a one-click Windows installer.
   - Bundle the database setup and app icon.
   - Include versioning and release notes.

4. Licensing and product files
   - Add a user-facing license and terms file.
   - Include a short user guide or quick-start guide.

## Suggested Build Order

If the goal is to make the app more saleable as quickly as possible, build in this order:

1. Full task editing
2. Search, filter, and sort
3. Dashboard summary cards
4. Backup and restore
5. Reminders and recurring tasks
6. Archive and undo
7. UI branding and packaging

## Best Sales Angle

The current codebase is closer to a task manager than a note-taking product. If you want stronger market appeal, you can position it in one of two ways:

- Task manager with notes and attachments
- Notes app with task tracking and reminders

The second option usually sells better if you add richer note editing, search, tags, and reminders.

## Short-Term Recommendation

The highest-value next release would be:

- Complete edit form for tasks
- Search and filter bar
- Dashboard counters
- Backup and restore
- A cleaner top-level layout
