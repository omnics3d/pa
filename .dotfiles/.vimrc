" --- ОСНОВНЫЕ СИСТЕМЫ ---
syntax on
filetype plugin indent on

" --- ИНТЕРФЕЙС ---
set number
set relativenumber 
set mouse=a
set noswapfile
set colorcolumn=80
set linebreak
set termguicolors " Включение 24-битного цвета

" --- ТАБУЛЯЦИЯ (Python-стандарт) ---
set tabstop=4
set shiftwidth=4
set expandtab

" --- ПОИСК ---
set hlsearch
set incsearch
set ignorecase
set smartcase

" --- ОТОБРАЖЕНИЕ СЛУЖЕБНЫХ СИМВОЛОВ ---
set list
set listchars=tab:›\ ,trail:•,extends:#,precedes:<

" --- ФОЛДИНГ (Сворачивание) ---
set foldenable
set foldmethod=marker
set foldmarker={{{,}}}
set foldnestmax=3
set foldcolumn=1
set foldlevel=0  " При открытии файла всё свёрнуто
"set foldopen=all  " Автоматическое открытие при поиске или вставке

" --- КАСТОМНЫЙ ВИД СВЕРНУТОЙ СТРОКИ ---
function! MyFoldText()
    let nl = v:foldend - v:foldstart + 1
    let linetext = getline(v:foldstart)
    let clean_text = substitute(linetext, '.*{{{', '', 'g')
    if clean_text =~ '^\s*$'
        let clean_text = getline(v:foldstart + 1)
    endif
    return '+ ' . substitute(clean_text, '^ *', '', '') . ' | строк: ' . nl
endfunction
set foldtext=MyFoldText()


" --- ЦВЕТА И ПОДСВЕТКА ---
" Сначала общие настройки
highlight Folded guibg=#020616 guifg=#375a63
highlight Statement guibg=#020616 guifg=#3475cc
highlight Comment guifg=#206C32 guibg=NONE gui=italic

" Специфичные настройки для Python
" Создаем группу для докстрингов, чтобы красить их отдельно
autocmd FileType python syn region pythonDocstring start=+^\s*[uU]\?[rR]\?"""+ end=+"""+ keepend excludenl
autocmd FileType python syn region pythonDocstring start=+^\s*[uU]\?[rR]\?'''+ end=+'''+ keepend excludenl

hi pythonDocstring guifg=#4D8059
hi pythonString guibg=#020616 guifg=#1391AB
hi pythonTripleQuotes guibg=#020616 guifg=#e1c0b6
hi pythonNumber guibg=#020616 guifg=#50819f
hi pythonQuotes guibg=#020616 guifg=#8f5b5b

" --- ГОРЯЧИЕ КЛАВИШИ ---
" Быстрое управление фолдами через Пробел (вместо zc/zo)
nnoremap <space> za

if &term =~ "screen" || &term =~ "xterm" || &term =~ "tmux" || &term =~ "alacritty"
    let &t_BE = "\e[?2004h"
    let &t_BD = "\e[?2004l"
    let &t_PS = "\e[200~"
    let &t_PE = "\e[201~"
endif


