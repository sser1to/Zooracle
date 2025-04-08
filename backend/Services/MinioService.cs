using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Minio;
using Minio.DataModel.Args;
using Minio.Exceptions;
using System;
using System.IO;
using System.Threading.Tasks;

namespace backend.Services
{
    public class MinioService : IMinioService
    {
        private readonly IMinioClient _minioClient;
        private readonly string _bucketName;
        private readonly ILogger<MinioService> _logger;
        private readonly string _externalEndpoint;

        public MinioService(IConfiguration configuration, ILogger<MinioService> logger)
        {
            _logger = logger;

            var minioConfig = configuration.GetSection("MinIO");
            var internalEndpoint = minioConfig["InternalEndpoint"];
            var externalEndpoint = minioConfig["ExternalEndpoint"];
            var accessKey = minioConfig["AccessKey"];
            var secretKey = minioConfig["SecretKey"];
            _bucketName = minioConfig["BucketName"];
            _externalEndpoint = externalEndpoint;

            _minioClient = new MinioClient()
                .WithEndpoint(internalEndpoint)
                .WithCredentials(accessKey, secretKey)
                .WithSSL(false)
                .Build();
        }

        public async Task<string> GetPresignedUrlAsync(string objectName, TimeSpan expiry)
        {
            // Используем внешний endpoint для presigned URL
            var clientWithExternalEndpoint = new MinioClient()
                .WithEndpoint(_externalEndpoint)
                .WithCredentials(_minioClient.Config.AccessKey, _minioClient.Config.SecretKey)
                .WithSSL(false)
                .Build();

            var presignedUrl = await clientWithExternalEndpoint.PresignedGetObjectAsync(
                new PresignedGetObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(objectName)
                    .WithExpiry((int)expiry.TotalSeconds));
            return presignedUrl;
        }

        public async Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType)
        {
            try
            {
                // Используем переданное имя файла без добавления нового GUID
                string objectName = fileName; // Больше не добавляем Guid.NewGuid()
                _logger.LogInformation("Загрузка файла: {ObjectName}, ContentType: {ContentType}", objectName, contentType);

                // Сбрасываем позицию потока
                fileStream.Position = 0;

                var putObjectArgs = new PutObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(objectName)
                    .WithStreamData(fileStream)
                    .WithObjectSize(fileStream.Length)
                    .WithContentType(contentType);

                await _minioClient.PutObjectAsync(putObjectArgs);

                // Формируем URL для доступа к файлу
                string fileUrl = $"{_minioClient.Config.Endpoint}/{_bucketName}/{objectName}";
                _logger.LogInformation("Файл успешно загружен. URL: {FileUrl}", fileUrl);

                return fileUrl;
            }
            catch (MinioException e)
            {
                _logger.LogError(e, "Ошибка при загрузке файла {FileName}", fileName);
                throw;
            }
        }

        public async Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType, bool isUpdate = false)
        {
            try
            {
                string objectName = isUpdate ? fileName : $"{Guid.NewGuid()}_{fileName}";
                _logger.LogInformation("Загрузка файла: {ObjectName}, ContentType: {ContentType}, IsUpdate: {IsUpdate}",
                    objectName, contentType, isUpdate);

                fileStream.Position = 0;

                var putObjectArgs = new PutObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(objectName)
                    .WithStreamData(fileStream)
                    .WithObjectSize(fileStream.Length)
                    .WithContentType(contentType);

                await _minioClient.PutObjectAsync(putObjectArgs);

                string fileUrl = $"{_minioClient.Config.Endpoint}/{_bucketName}/{objectName}";
                _logger.LogInformation("Файл успешно загружен. URL: {FileUrl}", fileUrl);

                return fileUrl;
            }
            catch (MinioException e)
            {
                _logger.LogError(e, "Ошибка при загрузке файла {FileName}", fileName);
                throw;
            }
        }

        public async Task RenameFileAsync(string oldObjectName, string newObjectName)
        {
            try
            {
                _logger.LogInformation("Переименование объекта в MinIO: {OldName} -> {NewName}",
                                      oldObjectName, newObjectName);

                // 1. Получить старый объект
                var memoryStream = new MemoryStream();
                var getObjectArgs = new GetObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(oldObjectName)
                    .WithCallbackStream(stream =>
                    {
                        stream.CopyTo(memoryStream);
                        memoryStream.Position = 0;
                    });

                await _minioClient.GetObjectAsync(getObjectArgs);

                // 2. Определить тип контента
                string contentType = GetContentType(Path.GetExtension(oldObjectName));

                // 3. Загрузить объект с новым именем
                var putObjectArgs = new PutObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(newObjectName)
                    .WithStreamData(memoryStream)
                    .WithObjectSize(memoryStream.Length)
                    .WithContentType(contentType);

                await _minioClient.PutObjectAsync(putObjectArgs);

                // 4. Удалить старый объект
                var removeObjectArgs = new RemoveObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(oldObjectName);

                await _minioClient.RemoveObjectAsync(removeObjectArgs);

                _logger.LogInformation("Объект успешно переименован в MinIO");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Ошибка при переименовании объекта в MinIO: {OldObjectName} -> {NewObjectName}",
                                oldObjectName, newObjectName);
                throw;
            }
        }

        private string GetContentType(string fileName)
        {
            var ext = Path.GetExtension(fileName).ToLowerInvariant();
            return ext switch
            {
                ".jpg" or ".jpeg" => "image/jpeg",
                ".png" => "image/png",
                ".gif" => "image/gif",
                ".pdf" => "application/pdf",
                ".doc" or ".docx" => "application/msword",
                ".xls" or ".xlsx" => "application/vnd.ms-excel",
                ".txt" => "text/plain",
                ".md" => "text/markdown",
                ".mp4" => "video/mp4",
                ".mp3" => "audio/mpeg",
                ".py" => "text/x-python",
                ".js" => "text/javascript",
                ".html" => "text/html",
                ".css" => "text/css",
                ".cs" => "text/x-csharp",
                _ => "application/octet-stream"
            };
        }

        public async Task<Stream> GetFileAsync(string objectName)
        {
            try
            {
                _logger.LogInformation("Получение файла из MinIO: {ObjectName}", objectName);

                var memoryStream = new MemoryStream();
                var getObjectArgs = new GetObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(objectName)
                    .WithCallbackStream(stream =>
                    {
                        stream.CopyTo(memoryStream);
                        memoryStream.Position = 0;
                    });

                await _minioClient.GetObjectAsync(getObjectArgs);
                return memoryStream;
            }
            catch (MinioException e)
            {
                _logger.LogError(e, "Ошибка при получении файла из MinIO: {ObjectName}", objectName);
                throw;
            }
        }

        public async Task DeleteFileAsync(string fileName)
        {
            try
            {
                _logger.LogInformation("Удаление файла: {FileName}", fileName);

                var removeObjectArgs = new RemoveObjectArgs()
                    .WithBucket(_bucketName)
                    .WithObject(fileName);

                await _minioClient.RemoveObjectAsync(removeObjectArgs);
                _logger.LogInformation("Файл {FileName} успешно удален", fileName);
            }
            catch (MinioException e)
            {
                _logger.LogError(e, "Ошибка при удалении файла {FileName}", fileName);
                throw;
            }
        }
    }

    public interface IMinioService
    {
        Task<string> UploadFileAsync(Stream fileStream, string fileName, string contentType, bool isUpdate = false);
        Task<Stream> GetFileAsync(string fileName);
        Task DeleteFileAsync(string fileName);
        Task RenameFileAsync(string oldFileName, string newFileName);
        Task<string> GetPresignedUrlAsync(string objectName, TimeSpan expiry);
    }
}
