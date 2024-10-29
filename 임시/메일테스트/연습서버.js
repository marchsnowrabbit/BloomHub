
const nodemailer = require('nodemailer');



var variable = "0,1,2,3,4,5,6,7,8,9,a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z".split(",");
var randomPassword = createRandomPassword(variable, 8);

 //비밀번호 랜덤 함수
 function createRandomPassword(variable, passwordLength) {
      var randomString = "";
      for (var j=0; j<passwordLength; j++) 
        randomString += variable[Math.floor(Math.random()*variable.length)];
         return randomString
       }



       const transporter = nodemailer.createTransport({
        service: 'gmail',
        port: 465,
        secure: true, // true for 465, false for other ports
        auth: { // 이메일을 보낼 계정 데이터 입력
          user: '@gmail.com',
          pass: 'password',
        },
      });
     const emailOptions = { // 옵션값 설정
          from: '@gmail.com',
          to: 'liyusang1@naver.com',
          subject: 'Binding에서 임시비밀번호를 알려드립니다.',
          html: 
          "<h1 >Binding에서 새로운 비밀번호를 알려드립니다.</h1> <h2> 비밀번호 : " + randomPassword + "</h2>"
          +'<h3 style="color: crimson;">임시 비밀번호로 로그인 하신 후, 반드시 비밀번호를 수정해 주세요.</h3>'
          +'<img src="https://firebasestorage.googleapis.com/v0/b/mangoplate-a1a46.appspot.com/o/mailImg.png?alt=media&token=75e07db2-5aa6-4cb2-809d-776ba037fdec">'		
          ,
        };
        transporter.sendMail(emailOptions, res); //전송