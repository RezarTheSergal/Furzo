function toggleComments() {
    const commentsSection = document.querySelector('.comments-insertion');
    const commentsOverlay = document.querySelector('.comments-overlay');
    const mainContent = document.querySelector('.main-content');
    if (commentsOverlay) {
        if (commentsOverlay.classList.contains('active')) {
            commentsSection.style.display = 'none';
            commentsOverlay.classList.remove('active');
            mainContent.classList.remove('comments-open');
        } else {
            commentsSection.style.display = 'block';
            commentsOverlay.classList.add('active');
            mainContent.classList.add('comments-open');
        }
    }
}

function openComments() {
    const commentsSection = document.querySelector('.comments-insertion');
    const commentsOverlay = document.querySelector('.comments-overlay');
    const mainContent = document.querySelector('.main-content');
    
    if (commentsOverlay) {
        commentsSection.style.display = 'block';
        commentsOverlay.classList.add('active');
        mainContent.classList.add('comments-open');
    }
}

function closeComments() {
    const commentsSection = document.querySelector('.comments-insertion');
    const commentsOverlay = document.querySelector('.comments-overlay');
    const mainContent = document.querySelector('.main-content');
    
    if (commentsOverlay) {
        commentsSection.style.display = 'none';
        commentsOverlay.classList.remove('active');
        mainContent.classList.remove('comments-open');
    }
}


function toggleReplies(commentId) {
    const repliesSection = document.getElementById(`replies-${commentId}`);
    const toggleButton = document.querySelector(`[data-comment-id="${commentId}"]`);

    if (repliesSection && toggleButton) {
        if (repliesSection.classList.contains('show')) {
            repliesSection.classList.remove('show');
            toggleButton.classList.remove('expanded');
        } else {
            repliesSection.classList.add('show');
            toggleButton.classList.add('expanded');
        }
    }
}

function toggleReplyForm(commentId) {
    const commentFormContainer = document.querySelector('.comment-form-container');
    const formTitle = commentFormContainer.querySelector('.form-title');
    const commentItem = document.querySelector(`[data-comment-item-id="${commentId}"]`);
    const submitButton = document.querySelector('.submit-btn');

    if (commentItem && formTitle) {
        if (commentItem.classList.contains('replying')) {
            commentItem.classList.remove('replying');
            submitButton.removeAttribute('data-comment-reply-to-id');
            formTitle.textContent = `Оставить комментарий`;
        } else {
            const replyItem = document.querySelectorAll('.comment-item.replying');
            replyItem.forEach(item => {
                if(item.classList.contains('replying')){
                    item.classList.remove('replying');
                }
            });
            commentItem.classList.add('replying');
            
            submitButton.setAttribute('data-comment-reply-to-id', `${commentId}`);
            const commentAutrhor = commentItem.querySelector('.comment-author').textContent;
            formTitle.textContent = `Ответ на комментарий от: ${commentAutrhor}`;
        }
    }
}


function setLoadingState(button, isLoading, text = null) {
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.classList.add('loading');
        
        if (!button.dataset.originalText) {
            button.dataset.originalText = button.textContent;
        }
        
        button.textContent = text || 'Загрузка...';
        
        if (!button.querySelector('.spinner')) {
            const spinner = document.createElement('span');
            spinner.className = 'spinner';
            spinner.innerHTML = '⟳';
            button.insertBefore(spinner, button.firstChild);
        }
    } else {
        button.disabled = false;
        button.classList.remove('loading');
        
        if (text) {
            button.textContent = text;
        } else if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
        }
        
        const spinner = button.querySelector('.spinner');
        if (spinner) {
            spinner.remove();
        }
    }
}

function showError(message) {
    let errorContainer = document.querySelector('.error-message');
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.className = 'error-message';
        document.body.appendChild(errorContainer);
    }
    
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
    
    setTimeout(() => {
        alert(message);
        errorContainer.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    let successContainer = document.querySelector('.success-message');
    if (!successContainer) {
        successContainer = document.createElement('div');
        successContainer.className = 'success-message';
        document.body.appendChild(successContainer);
    }
    
    successContainer.textContent = message;
    successContainer.style.display = 'block';
    
    setTimeout(() => {
        successContainer.style.display = 'none';
    }, 3000);
}

let formHandlerAttached = false;

function attachCommentFormHandler(postId) {
    console.log('Подключение обработчика формы для поста:', postId);
    
    const form = document.getElementById('main-comment-form');
    if (form) {
        console.log('Форма найдена, подключаем обработчик');
        

        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        
        newForm.addEventListener('submit', function(event) {
            console.log('Форма отправлена для поста:', postId);
            event.preventDefault();
            event.stopPropagation();
            submitComment(event, postId);
        });
        
        window.formHandlerAttached = true;
        console.log('Обработчик формы успешно подключен');
    } else {
        console.log('Форма не найдена');
    }
}

function attachCommentsEventHandlers() {
    console.log('Подключение обработчиков событий комментариев');

    const toggleButtons = document.querySelectorAll('.toggle-replies-btn');
    toggleButtons.forEach(button => {
        const commentId = button.getAttribute('data-comment-id');
        button.onclick = function() {
            toggleReplies(commentId);
        };
    });
    
    const replyButtons = document.querySelectorAll('.reply-btn');
    replyButtons.forEach(button => {
        const commentId = button.getAttribute('data-comment-reply-id');
        button.onclick = function() {
            toggleReplyForm(commentId);
        };
    });
    
    const comments = document.querySelectorAll('.comment-item');
    comments.forEach((comment, index) => {
        comment.style.animationDelay = `${index * 0.1}s`;
    });
    
    console.log('Обработчики событий комментариев подключены');
}

function handleToggleReplies(event) {
    const commentId = this.getAttribute('data-comment-id');
    toggleReplies(commentId);
}

function handleReplyClick(event) {
    const commentId = this.getAttribute('data-comment-reply-id');
    toggleReplyForm(commentId);
}

async function refreshCommentsBlock(postId) {
    const result = await window.sendRequest('/comments/', {
        post_id: postId,
    });

    if (result && result.success) {
        const html = result.html;

        document.querySelector('.comments-insertion').innerHTML = html;
        const commentsOverlay = document.querySelector('.comments-overlay');
    
        if (commentsOverlay) {
            commentsOverlay.classList.add('active');
        }
        
        window.formHandlerAttached = false;
        attachCommentFormHandler(postId);
        attachCommentsEventHandlers();
        
        showSuccess('Комментарии успешно обновлены');
    }
    else
    {
        console.error('Error:', result.error );
        showError('Ошибка при обновлении комментариев: ' + (result.error || 'Неизвестная ошибка'));
    }
}

function incrementCommentsCount() {
    const commentBtn = document.querySelector('.stat-item.comment');
    if (!commentBtn) return;

    const countElem = commentBtn.querySelector('.stat-count');

    if (countElem) {
        let count = parseInt(countElem.textContent, 10) || 0;
        countElem.textContent = count + 1;
    }
}

async function submitComment(event, postId) {
    event.preventDefault();
    event.stopPropagation();
    
    console.log('submitComment called with postId:', postId);
    
    const form = event.target;
    const submitBtn = form.querySelector('.submit-btn');
    const textarea = form.querySelector('textarea');
    
    if (!textarea.value.trim()) {
        showError('Комментарий не может быть пустым');
        return;
    }

    const parentCommentId = submitBtn.getAttribute("data-comment-reply-to-id");
    
    setLoadingState(submitBtn, true, 'Отправка...');
    
    try {
        const result = await window.sendRequest('/add_comment/', {
            post_id: postId,
            parent_comment_id: parentCommentId,
            content: textarea.value,
        });

        if (result && result.success) {
            await refreshCommentsBlock(postId);
            incrementCommentsCount();
            form.reset();

            const emptyState = document.querySelector('.comments-empty');
            if (emptyState) {
                emptyState.style.display = 'none';
            }
                
            showSuccess('Комментарий успешно добавлен');
        }
        else
        {
            console.error('Error:', result.error );
            showError('Ошибка при отправке комментария: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Submit error:', error);
        showError('Ошибка при отправке комментария: ' + error.message);
    }

    setLoadingState(submitBtn, false, 'Отправить');
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - comments.js');

    attachCommentsEventHandlers();
    
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeComments();
        }
    });

    const form = document.getElementById('main-comment-form');
    if (form) {
        const postId = parseInt(form.dataset.postId);
        console.log('Form found with postId:', postId);
        
        window.formHandlerAttached = false;
        attachCommentFormHandler(postId);
    }
});

window.openComments = openComments;
window.closeComments = closeComments;
window.toggleReplies = toggleReplies;
window.toggleReplyForm = toggleReplyForm;
window.submitComment = submitComment;
window.refreshCommentsBlock = refreshCommentsBlock;
window.attachCommentFormHandler = attachCommentFormHandler;
window.attachCommentsEventHandlers = attachCommentsEventHandlers;
window.formHandlerAttached = formHandlerAttached;