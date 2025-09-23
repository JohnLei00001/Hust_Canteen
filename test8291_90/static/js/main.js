// 注册表单验证
function validateForm() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    
    if (username.length < 3) {
        alert('用户名至少需要3个字符!');
        return false;
    }
    
    if (password.length < 6) {
        alert('密码至少需要6个字符!');
        return false;
    }
    
    if (password !== confirmPassword) {
        alert('两次输入的密码不一致!');
        return false;
    }
    
    return true;
}

// 个人中心表单验证
function validateProfileForm() {
    const newPassword = document.getElementById('new_password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    
    if (newPassword && newPassword.length < 6) {
        alert('新密码至少需要6个字符!');
        return false;
    }
    
    if (newPassword && newPassword !== confirmPassword) {
        alert('两次输入的新密码不一致!');
        return false;
    }
    
    return true;
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 如果是个人中心页面，绑定表单验证
    if (document.querySelector('.profile-form')) {
        document.querySelector('.profile-form').onsubmit = validateProfileForm;
    }
});