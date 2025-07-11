async function scroll(direction) {
    if (typeof window.csrftoken === 'undefined') {
        console.error('CSRF token не найден');
        return;
    }

    const form = document.getElementById('main-comment-form');
    if (!form) {
        console.error('Форма комментариев не найдена');
        return;
    }

    const currentPostId = parseInt(form.dataset.postId);
    if (isNaN(currentPostId)) {
        console.error('Некорректный ID поста');
        return;
    }

    const comments = document.querySelector('.main-content');
    if (!comments) {
        console.error('Мейн контент не обнаружен');
        return;
    }
    const is_comments_active = comments.classList.contains("comments-open");

    try {
        const result = await window.sendRequest('/get-post/', {
            post_id: currentPostId,
            direction: direction,
        });

        if (result && result.success) {
            console.info('Пост успешно загружен');
            
            const mainElement = document.querySelector('main');
            if (mainElement) {
                mainElement.innerHTML = result.html;
                
                if (is_comments_active) {
                    window.openComments();
                }

                initializeEventHandlers();
                initializeCommentHandlers();
                
                if (result.post_id && window.history && window.history.pushState) {
                    const newUrl = window.location.pathname + '?post=' + result.post_id;
                    window.history.pushState({postId: result.post_id}, '', newUrl);
                }
            }
        } else {
            console.error('Ошибка загрузки поста:', result?.error || 'Неизвестная ошибка');
        }
    } catch (error) {
        console.error('Ошибка при переключении поста:', error);
    }
}

function initializeEventHandlers() {
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        const userReaction = mainContent.dataset.userReaction;
        
        if (userReaction === 'like') {
            const likeButton = document.querySelector('.stat-item.like');
            if (likeButton) {
                const icon = likeButton.querySelector('.stat-icon');
                if (icon) icon.textContent = '💖';
                likeButton.classList.add('active');
                likeButton.style.background = 'rgba(34, 197, 94, 0.8)';
            }
        } else if (userReaction === 'dislike') {
            const dislikeButton = document.querySelector('.stat-item.dislike');
            if (dislikeButton) {
                const icon = dislikeButton.querySelector('.stat-icon');
                if (icon) icon.textContent = '💥';
                dislikeButton.classList.add('active');
                dislikeButton.style.background = 'rgba(239, 68, 68, 0.8)';
            }
        }
    }
}

function initializeCommentHandlers() {
    console.log('Инициализация обработчиков комментариев');
    
    window.formHandlerAttached = false;
    
    const form = document.getElementById('main-comment-form');
    if (form) {
        const postId = parseInt(form.dataset.postId);
        console.log('Найдена форма с postId:', postId);  

        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        
        newForm.addEventListener('submit', function(event) {
            event.preventDefault();
            event.stopPropagation();
            console.log('Форма отправлена для поста:', postId);
            if (typeof window.submitComment === 'function') {
                window.submitComment(event, postId);
            }
        });
        
        window.formHandlerAttached = true;
        console.log('Обработчик формы успешно подключен');
    }
    
    const replyButtons = document.querySelectorAll('.reply-btn');
    replyButtons.forEach(button => {
        const commentId = button.getAttribute('data-comment-reply-id');
        button.onclick = function() {
            if (typeof window.toggleReplyForm === 'function') {
                window.toggleReplyForm(commentId);
            }
        };
    });
    
    const toggleButtons = document.querySelectorAll('.toggle-replies-btn');
    toggleButtons.forEach(button => {
        const commentId = button.getAttribute('data-comment-id');
        button.onclick = function() {
            if (typeof window.toggleReplies === 'function') {
                window.toggleReplies(commentId);
            }
        };
    });
    
    const closeBtn = document.querySelector('.close-comments-btn');
    if (closeBtn) {
        closeBtn.onclick = function() {
            if (typeof window.closeComments === 'function') {
                window.closeComments();
            }
        };
    }
}

let isHoveringImg = false;
let scrollCooldown = false;
const SCROLL_COOLDOWN_TIME = 100;

document.addEventListener('DOMContentLoaded', function() {
    const imgContainer = document.querySelector('.img-container');
    const bottomOverlay = document.querySelector('.tags-section');

    if (!imgContainer) {
        console.error('Картинковый элемент не найден');
        return;
    }

    if (!bottomOverlay) {
        console.error('Нижний элемент не найден');
        return;
    }

    imgContainer.addEventListener('mouseenter', function() {
        isHoveringImg = true;
    });

    imgContainer.addEventListener('mouseleave', function() {
        isHoveringImg = false;
    });

    document.addEventListener('keydown', async function(event) {
        if (!isHoveringImg || scrollCooldown) return;

        switch (event.key) {
            case "ArrowUp":
                event.preventDefault();
                scrollCooldown = true;
                await scroll(-1);
                setTimeout(() => { scrollCooldown = false; }, SCROLL_COOLDOWN_TIME);
                break;
            case "ArrowDown":
                event.preventDefault();
                scrollCooldown = true;
                await scroll(1);
                setTimeout(() => { scrollCooldown = false; }, SCROLL_COOLDOWN_TIME);
                break;
        }
    });

    initializeEventHandlers();
    initializeCommentHandlers();

    window.addEventListener('popstate', function(event) {
        if (event.state && event.state.postId) {

            const postId = parseInt(event.state.postId);
            if (!isNaN(postId)) {
                loadSpecificPost(postId);
            }
        }
    });
});

async function loadSpecificPost(postId) {
    try {
        const result = await window.sendRequest('/get-specific-post/', {
            post_id: postId
        });

        if (result && result.success) {
            const mainElement = document.querySelector('main');
            if (mainElement) {
                mainElement.innerHTML = result.html;
                initializeEventHandlers();
                initializeCommentHandlers();
            }
        }
    } catch (error) {
        console.error('Ошибка при загрузке конкретного поста:', error);
    }
}

window.scroll = scroll;
window.initializeEventHandlers = initializeEventHandlers;
window.initializeCommentHandlers = initializeCommentHandlers;