// static/js/notifications.js
document.addEventListener('DOMContentLoaded', function() {
    // Récupérer le token CSRF depuis la balise meta
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // Marquer une notification comme lue via AJAX (utilisé dans la navbar et la page notifications)
    window.markNotificationAsRead = function(event, notificationId) {
        event.preventDefault();
        fetch(`/users/mark-notification-read/${notificationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Mettre à jour l'élément dans la page notifications
                const notificationItem = document.querySelector(`.notification-item[data-notification-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.classList.remove('unread');
                    const markReadButton = notificationItem.querySelector('.mark-read');
                    if (markReadButton) markReadButton.remove();
                }
                // Mettre à jour l'élément dans la navbar
                const navbarNotificationItem = document.querySelector(`a[data-notification-id="${notificationId}"]`);
                if (navbarNotificationItem) {
                    navbarNotificationItem.classList.remove('text-bold');
                }
                // Mettre à jour le badge de notifications non lues dans la navbar
                const unreadBadge = document.querySelector('#notificationsDropdown .badge');
                const currentCount = parseInt(unreadBadge ? unreadBadge.textContent : 0);
                if (currentCount > 1) {
                    unreadBadge.textContent = currentCount - 1;
                } else {
                    unreadBadge?.remove();
                }
            }
        })
        .catch(error => console.error('Error:', error));
    };

    // Marquer une notification comme lue via le bouton "Marquer comme lu" (page notifications)
    document.querySelectorAll('.mark-read').forEach(button => {
        button.addEventListener('click', function() {
            const notificationId = button.dataset.notificationId;
            markNotificationAsRead({ preventDefault: () => {} }, notificationId);
        });
    });

    // Supprimer une notification via AJAX (page notifications)
    document.querySelectorAll('.delete-notification').forEach(button => {
        button.addEventListener('click', function() {
            if (confirm('Êtes-vous sûr de vouloir supprimer cette notification ?')) {
                const notificationId = button.dataset.notificationId;
                fetch(`/users/delete-notification/${notificationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        button.closest('.notification-item').remove();
                    } else {
                        alert('Erreur lors de la suppression de la notification.');
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    });

    // Marquer toutes les notifications comme lues via AJAX (page notifications)
    const markAllReadButton = document.getElementById('mark-all-read');
    if (markAllReadButton) {
        markAllReadButton.addEventListener('click', function() {
            fetch('/users/mark-all-notifications-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.querySelectorAll('.notification-item.unread').forEach(item => {
                        item.classList.remove('unread');
                        const markReadButton = item.querySelector('.mark-read');
                        if (markReadButton) markReadButton.remove();
                    });
                    // Mettre à jour le badge dans la navbar
                    const unreadBadge = document.querySelector('#notificationsDropdown .badge');
                    if (unreadBadge) unreadBadge.remove();
                } else {
                    alert('Erreur lors de la mise à jour des notifications.');
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }
});