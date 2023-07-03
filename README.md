# Mini-Exchange-Stock-Server
(phiên bản hiện tại 0.2)

## Tổng quan
- Mục đích chính của dự án nhằm nắm rõ về giao thức TCP/UDP.
- Ngôn ngữ lập trình Python
- Cơ sở dữ liệu: SQL Server
- Hỗ trợ multiclient, cho phép nhiều request gửi tới Server cùng lúc
- Được thực hiện trong môi trường local

## Chức năng 
Mini-Exchange-Stock-Server, có thể hiểu là một Hệ thống giao dịch trực tiếp, với các tính năng:
- Cho phép nhà đầu tư giao dịch và theo dõi thông tin thị trường trực tiếp thông qua kết nối socket với sàn giao dịch.
- Nhà đầu tư có thể đặt lệnh mua/bán, hủy lệnh và theo dõi lịch sử giao dịch.
- Hỗ trợ multiclient, cho phép cung cấp nội dung khác nhau đến các domain khác nhau.
- Server có thể nhận các thông tin lệnh mua/bán từ client và trả về thông tin cho client (Khớp lệnh, Lệnh đã được chấp thuận bởi server, reject bởi server):
  - Kiểm tra khi client gửi order tới:
    - mã cổ phiểu
    - trường hợp bán: số lượng cổ phiếu hiện có có đủ để bán không (số lượng cổ phiểu trong data >= số lượng bán)
    - trường hợp mua: số dư trong tài khoản có đủ để mua không (số dư > số lượng cổ phiếu mua * giá tiền)
    - nếu tất cả các trường hợp thỏa mãn thì thêm order vào db
  - Thay đổi số dư của tài khoản khi có giao dịch
- Client:
  - Đăng nhập, đăng xuất
  - Gửi các thông tin lệnh mua bán đến server
  - Lấy thông tin lịch sử giao dịch từ server, trạng thái order, số dư trong tài khoản
- ...
