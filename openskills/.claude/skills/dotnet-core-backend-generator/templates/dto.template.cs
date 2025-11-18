namespace Backend.Application.DTOs
{
    public record {{EntityName}}CreateDto
    {
        // properties for creation
    }

    public record {{EntityName}}UpdateDto
    {
        public int Id { get; init; }
        // properties for update
    }

    public record {{EntityName}}ResponseDto
    {
        public int Id { get; init; }
        // response properties
        public DateTime CreatedAt { get; init; }
    }
}
