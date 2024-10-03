ISC 프로젝트를 위한 작업 공간 입니다.

현재 main 브렌치만 사용


-db playground 사용법 모름 -> 몰라도 될듯?
-몽고디비 - url mongodb+srv://<db_username>:<db_password>@cluster0.6twyc.mongodb.net/


-사진 관련해서 DB를 쓰려면 좀 어려울듯?
MongoDB에 이미지를 저장하는 방법은 크게 두 가지가 있습니다:

이미지 데이터를 직접 MongoDB에 저장하는 방법: 이미지를 Base64 형식으로 변환하여 MongoDB에 저장하거나, MongoDB의 GridFS 기능을 사용하여 대용량 파일을 저장하는 방법입니다.

이미지 파일을 파일 시스템 또는 외부 저장소에 저장하고, 해당 파일 경로를 MongoDB에 저장하는 방법: 이미지 파일 자체는 다른 스토리지 서비스(예: AWS S3, Google Cloud Storage)에 저장하고, 그 경로(URL)만 MongoDB에 저장하는 방식입니다.


-flask_db_연결어쩌고.py -> 이거 안해본거 터치 ㄴㄴ
