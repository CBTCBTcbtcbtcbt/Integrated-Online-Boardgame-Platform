  $('#back-to-login-btn').click(() => {
  location.href = '/';
  console.log("返回登录页面");
  });
// 注册按钮事件
  $('#register-submit-btn').click(() => {
      const account = $('#register-account').val();
      const password = $('#register-password').val();
      const id = $('#register-id').val();
      
      if (!account || !password || !id) {
          $('#register-message').text('账号、密码和游戏ID不能为空');
          return;
      }
      
      // 调用注册API
      $.ajax({
          url: '/registerAPI',
          type: 'POST',
          contentType: 'application/json',
          data: JSON.stringify({ account, password, ID: id }),
          success: (response) => {
              if (response.ok) {
                  $('#register-message').removeClass('message').addClass('success-message');
                  $('#register-message').text('注册成功，请登录');
                  setTimeout(() => {
                      location.href = '/';
                  }, 2000);
              } else {
                  $('#register-message').text(response.msg);
              }
          },
          error: () => {
              $('#register-message').text('注册失败，请稍后重试');
          }
      });
  });

