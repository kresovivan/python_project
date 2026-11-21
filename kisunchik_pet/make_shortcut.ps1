$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('C:\Users\kresovivan\Desktop\Kisunchik.lnk')
$sc.TargetPath = 'C:\Users\kresovivan\AppData\Local\Programs\Python\Python314\pythonw.exe'
$sc.Arguments = '"C:\Python\PythonProject\python_project\kisunchik_pet\run.py"'
$sc.WorkingDirectory = 'C:\Python\PythonProject\python_project\kisunchik_pet'
$sc.IconLocation = 'C:\Python\PythonProject\python_project\kisunchik_pet\assets\icon.ico'
$sc.Description = 'Kisunchik desktop pet'
$sc.Save()
Write-Output "shortcut created"
