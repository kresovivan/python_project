$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('C:\Users\kresovivan\Desktop\Kisunchik.lnk')
$sc.TargetPath = 'C:\Python\PythonProject\python_project\kisunchik_pet\app\KisunchikPet.exe'
$sc.WorkingDirectory = 'C:\Python\PythonProject\python_project\kisunchik_pet\app'
$sc.Description = 'Kisunchik desktop pet'
$sc.Save()
Write-Output "shortcut created"
