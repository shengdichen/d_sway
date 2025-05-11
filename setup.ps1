function ConfigGlaze
{
    Copy-Item ".\windows\glaze\config.yaml" "$HOME\.glzr\glazewm\." -Force
}

function ConfigKomo
{
    Copy-Item ".\windows\komorebi\whkdrc" "$HOME\.config\." -Force

    $p = "$HOME\.config\komorebi"
    Copy-Item ".\windows\komorebi\komorebi.json" "$p\." -Force
    Copy-Item ".\windows\komorebi\komorebi.bar.json" "$p\." -Force
}

ConfigGlaze
ConfigKomo
