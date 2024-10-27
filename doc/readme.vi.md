# mupl - MangaDex Bulk Uploader
Tải hàng loạt thư mục và lưu trữ (.zip/.cbz) lên MangaDex một cách nhanh chóng và dễ dàng.

Đọc phần này bằng các ngôn ngữ khác: [Tiếng Anh](/readme.md)

***Sẽ có một bản phát hành cho mỗi ngôn ngữ, bao gồm tiếng Anh trong mỗi bản. Để tải xuống tất cả các ngôn ngữ, hãy tải tệp nguồn zip.***

## Mục lục
- [Cách sử dụng](#cách-sử-dụng)
  - [Tải xuống](#tải-xuống)
  - [Cài đặt](#cài-đặt)
  - [Chạy](#chạy)
  - [Cập nhật](#cập-nhật)
  - [Đối số dòng lệnh](#đối-số-dòng-lệnh)
- [Cấu trúc tên tệp tải lên](#cấu-trúc-tên-tệp)
  - [Quy ước đặt tên](#quy-ước-đặt-tên)
  - [Tham số tên](#tham-số-tên)
  - [Định dạng hình ảnh được chấp nhận](#định-dạng-hình-ảnh-được-chấp-nhận)
  - [Kích thước hình ảnh](#kích-thước-hình-ảnh)
    - [Tách ảnh](#tách-ảnh)
    - [Gộp ảnh](#gôp-ảnh)
- [Tập tin cấu hình](#cấu-hình)
  - [Tùy chọn người dùng](#tuỳ-chọn)
  - [Thông tin đăng nhập MangaDex](#thông-tin-đăng-nhập)
  - [Đường dẫn chương trình](#đường-dẫn)
- [Tệp tên-id](#tên-id)
  - [Ví dụ về tệp tên-id](#ví-dụ)
- [Đóng góp](#đóng-góp)
- [Dịch thuật](#dịch-thuật)


## Cách sử dụng
### Trình tải này được thử nghiệm cho Python 3.10+.


### Tải xuống
Tải xuống [phiên bản mới nhất](https://github.com/ArdaxHz/mupl/releases/latest) từ trang phát hành.

Giải nén tệp vào một thư mục và mở cửa sổ terminal mới. Trên terminal, điều hướng đến thư mục đã tạo bằng cách sử dụng `cd "<đường_dẫn_đến_thư_mục>"`.

### Cài đặt

Trước khi chạy trình tải lên, bạn sẽ cần cài đặt các mô-đun cần thiết. Để cài đặt các mô-đun, hãy chạy lệnh `pip install -r requirements.txt`, sử dụng `pip3` nếu bạn dùng macOS hoặc Linux thay vì `pip`.

Trong thư mục bạn đã giải nén, tạo hai thư mục tên là `to_upload` và `uploaded`.

### Chạy

Để chạy trình tải lên, trong cửa sổ terminal, sử dụng `python mupl.py` để bắt đầu. Sử dụng `python3` nếu chạy trên macOS hoặc Linux.

### Cập nhật

Trình cập nhật sẽ tự động kiểm tra khi bắt đầu chương trình nếu có phiên bản mới trên trang phát hành. Nếu có phiên bản mới, chương trình sẽ nhắc bạn cập nhật.

Nếu bạn muốn vô hiệu hóa trình cập nhật, bạn có thể thêm `--update` vào các tham số dòng lệnh. Ví dụ: `python mupl.py --update`.

### Đối số dòng lệnh
Có các đối số dòng lệnh có thể thêm sau lệnh chính để thay đổi hành vi của chương trình, ví dụ: `python mupl.py -t`.

##### Tùy chọn:
- `--update` `-u` Không kiểm tra bản cập nhật mới khi bắt đầu chương trình.
- `--verbose` `-v` Làm cho các thông báo và nhật ký dòng lệnh chi tiết hơn.
- `--threaded` `-t` Chạy trình tải lên theo luồng. *Mặc định: False*
- `--combine` `-c` Kết hợp các hình ảnh nhỏ hơn hoặc bằng 128px với hình ảnh trước đó. *Mặc định: False*

## Cấu trúc tên tệp
#### Quy ước đặt tên
`manga_title [lang] - cXXX (vYY) (chapter_title) {publish_date} [group]`

#### Tham số tên
- `manga_title` Tiêu đề manga (giống như khóa trong `name_id_map.json`) hoặc ID của MangaDex.
- `[lang]` Mã ngôn ngữ theo định dạng ISO. *Bỏ qua cho tiếng Anh.*
- `cXXX` Số chương. *Bỏ tiền tố "c" nếu chương là oneshot, ví dụ `cXXX > XXX`.*
- `(vYY)` Tập của chương. *Tùy chọn.*
- `(chapter_title)` Tiêu đề chương. Dùng `{question_mark}` thay cho dấu hỏi `?`. *Tùy chọn.*
- `{publish_date}` Ngày phát hành chương trong tương lai từ phía MangaDex. ***BẮT BUỘC** phải ở định dạng `YYYY-MM-DDTHH-MM-SS` nếu có.* *Tùy chọn.*
- `[group]` Danh sách tên nhóm hoặc ID. Nếu là tên nhóm thì chúng phải được đưa vào `name_id_map.json` cho ID. *Thêm nhiều nhóm bằng dấu cộng `+`.* *Tùy chọn.*

#### Định dạng hình ảnh được chấp nhận
- `png`
- `jpg`/`jpeg`
- `gif`
- `webp` *Sẽ được chuyển đổi thành png, jpg hoặc gif trong quá trình tải lên. Điều này không thay đổi tệp cục bộ.*

#### Kích thước hình ảnh
##### Tách ảnh
Hình ảnh không được vượt quá `10,000px` về chiều rộng hoặc chiều cao. Để chia hình ảnh thành các phần nhỏ hơn, ID manga phải nằm trong mảng `longstrip` hoặc `widestrip` trong bản đồ ID manga, được minh họa [bên dưới](#tên-id).

Nếu thiếu ID thì hình ảnh sẽ không được tách và **SẼ** bị bỏ qua.

##### Gộp ảnh
Nếu `--combine` được sử dụng, các hình ảnh nhỏ hơn hoặc bằng `128px` sẽ được kết hợp với hình ảnh trước đó **NẾU** chúng có cùng chiều rộng hoặc chiều cao với hình ảnh trước đó (tùy thuộc vào việc hình ảnh thuộc loại `longstrip` hay `widestrip`).

Nếu không được sử dụng hoặc các hình ảnh không có cùng chiều rộng hoặc chiều cao với hình ảnh trước đó, hình ảnh **SẼ** bị bỏ qua.


## Cấu hình
Cài đặt có thể thay đổi của người dùng có sẵn trong tệp `config.json`. Đây cũng là nơi bạn đặt thông tin đăng nhập MangaDex của mình.
Sao chép và bỏ `.example` khỏi `config.json.example` để bắt đầu sử dụng tệp cấu hình.

*Lưu ý: Các giá trị JSON không thể để trống và loại giá trị rất quan trọng.*
- Dùng (`null`) cho giá trị rỗng.
- Văn bản phải có dấu ngoặc kép (`"username"`)
- Số phải để một mình (`1.1`)


#### Tuỳ chọn
- `number_of_images_upload` Số lượng hình ảnh tải lên cùng một lúc. *Mặc định: 10*
- `upload_retry` Số lần thử tải lại hình ảnh hoặc chương. *Mặc định: 3*
- `ratelimit_time` Thời gian nghỉ (tính bằng giây) sau các lần gọi API. *Mặc định: 2*
- `max_log_days` Số ngày lưu trữ nhật ký. *Mặc định: 30*
- `group_fallback_id` ID nhóm sử dụng nếu không tìm thấy trong tệp hoặc bản đồ ID, để trống nếu không tải lên nhóm.  *Mặc định: null*
- `number_threads`: Số luồng để tải hình ảnh đồng thời. **Điều này có thể làm bạn bị hạn chế số lượng request.** Các luồng bị giới hạn từ 1-3. *Mặc định: 3*
- `language`: Ngôn ngữ cho các thông báo dòng lệnh. *Mặc định: en*

#### Thông tin đăng nhập
***Các giá trị này không thể để trống, nếu không trình tải lên sẽ không chạy.***
- `mangadex_username` Tên người dùng MangaDex.
- `mangadex_password` Mật khẩu MangaDex.
- `client_id` Client ID cho API MangaDex.
- `client_secret` Client Secret cho API MangaDex.

#### Đường dẫn
*Các tùy chọn này có thể để nguyên, không cần thay đổi.*
- `name_id_map_file` Tên tệp cho tên-id. *Mặc định: name_id_map.json*
- `uploads_folder` Thư mục để lấy các tệp mới tải lên. *Mặc định: to_upload*
- `uploaded_files` Thư mục để di chuyển các chương đã tải lên. *Mặc định: uploaded*
- `mangadex_api_url` URL API MangaDex. *Mặc định: https://api.mangadex.org*
- `mangadex_auth_url` URL xác thực MangaDex. *Mặc định: https://auth.mangadex.org/realms/mangadex/protocol/openid-connect*
- `mdauth_path` Tệp lưu cục bộ cho token đăng nhập MangaDex. *Mặc định: .mdauth*

<details>
  <summary>Cách lấy Client ID và Secret.</summary>

  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_1.png?raw=true)
  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)
</details>
<br />


## Tên-ID
Tệp `name_id_map.json` có định dạng sau:
```json
{
    "manga": {
        "hyakkano": "efb4278c-a761-406b-9d69-19603c5e4c8b"
    },
    "group": {
        "XuN": "b6d57ade-cab7-4be7-b2b8-be68484b3ad3"
    },
    "formats": {
        "longstrip": ["efb4278c-a761-406b-9d69-19603c5e4c8b"],
        "widestrip": ["69b4df2d-5ca3-4e58-91bd-74827629dcce"]
    }
}
```
Tệp chứa bản đồ tên-ID cho manga và nhóm tải lên tương ứng. Tên nên giống với tệp tải lên. Để tránh các vấn đề khi tải lên, hãy sử dụng tên viết thường và không có dấu cách.

Mỗi cặp tên-id mới nên được phân tách bằng dấu phẩy ở cuối dòng và dấu hai chấm giữa tên và ID. Cặp cuối cùng không có dấu phẩy.

`formats` chứa một danh sách các ID cho các định dạng là `longstrip` (hình ảnh dài) hoặc `widestrip` (hình ảnh rộng). Có thể có nhiều ID trong mỗi mảng, nhưng không được phép trùng lặp bất kì ID nào.

#### Ví dụ

Giả sử tôi muốn tải chương `hyakkano - c025 (v04) [XuN].cbz`. In my `name_id_map.json`, Trong `name_id_map.json`, tôi có khóa `hyakkano` và giá trị `efb4278c-a761-406b-9d69-19603c5e4c8b` cho manga ID để tải lên. Tôi cũng có `XuN` trong bản đồ nhóm với giá trị `b6d57ade-cab7-4be7-b2b8-be68484b3ad3`.

Chương trình sẽ tìm khóa `hyakkano` và `XuN` trong tệp này cho các ID được gán.

Nếu tôi có tệp tên là `efb4278c-a761-406b-9d69-19603c5e4c8b [es] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]`, chương trình sẽ lấy id manga trực tiếp từ tập tin, ngôn ngữ là tiếng Tây Ban Nha với mã `es`, số chương là null (oneshot) và không có tập (volume), tiêu đề chương là `Momi-san` với các nhóm `XuN` (id lấy từ `name_id_map.json`) và `00e03853-1b96-4f41-9542-c71b8692033b`.


## Đóng góp
- Hãy đảm bảo không có vấn đề nào trùng lặp trước khi mở một vấn đề mới.
- Yêu cầu pull có thể được mở nếu bạn cho rằng cần thiết, nhưng vui lòng định dạng mã với Python Black (cài đặt mặc định) trước khi thực hiện.

### Dịch thuật
Có hai tệp cần dịch, tệp readme này và tệp [mupl/loc/en.json](mupl/loc/en.json).

- README đã dịch nên được đặt trong thư mục [doc/](doc/) với tên `readme.<mã_ngôn_ngữ>.md` theo định dạng mã ngôn ngữ ISO, ví dụ: `readme.pt-br.md`. Cập nhật README của bạn để liên kết lại với README này dưới danh sách "Đọc điều này bằng các ngôn ngữ khác".
- Tệp json đã dịch nên được đặt tên `<mã_ngôn_ngữ>.json` với định dạng mã ngôn ngữ ISO và đặt trong thư mục [mupl/loc/](mupl/loc/), ví dụ: `pt-br.json`. 

Sau khi dịch các tệp này, hãy cập nhật README này với liên kết đến README của bạn đã dịch. Vui lòng gửi PR với những thay đổi này.
