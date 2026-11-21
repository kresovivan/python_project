$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('C:\Users\kresovivan\Desktop\Kisunchik.lnk')
$sc.TargetPath = 'C:\Python\PythonProject\python_project\kisunchik_pet\KisunchikPet.exe'
$sc.WorkingDirectory = 'C:\Python\PythonProject\python_project\kisunchik_pet'
$sc.Description = 'Kisunchik desktop pet'
$sc.Save()
Write-Output "shortcut created"
