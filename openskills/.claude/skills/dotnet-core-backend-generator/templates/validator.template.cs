using FluentValidation;

namespace Backend.Application.Validators
{
    public class {{EntityName}}CreateDtoValidator : AbstractValidator<{{EntityName}}CreateDto>
    {
        public {{EntityName}}CreateDtoValidator()
        {
            // Add validation rules here
            // RuleFor(x => x.Name).NotEmpty().MaximumLength(100);
        }
    }
}
