namespace Backend.Domain.Entities
{
    public class {{EntityName}}
    {
        public int Id { get; set; }
        // Properties from user input

        public DateTime CreatedAt { get; set; }
        public DateTime? UpdatedAt { get; set; }
        public string CreatedBy { get; set; } = string.Empty;
        public string? UpdatedBy { get; set; }
        public bool IsDeleted { get; set; }

        // Navigation properties
    }
}
